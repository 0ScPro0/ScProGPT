import { apiClient } from './client';

async function fetchWithAuth(url, options) {
    const response = await fetch(url, options);

    // One retry with a token refresh for expired access cookies
    if (response.status === 401) {
        const refresh = await fetch('/api/v1/auth/refresh', {
            method: 'POST',
            credentials: 'include',
        });
        if (refresh.ok) {
            return fetch(url, options);
        }
    }

    return response;
}

/**
 * Incremental SSE parser: splits raw text into "data:"/"event:" events.
 */
function createSseProcessor({ onChunk, onComplete, onError }) {
    let buffer = '';
    let chunksCount = 0;
    let completed = false;
    let errored = false;

    // Normalize line endings: SSE events may arrive with LF, CRLF or CR
    const normalize = (text) =>
        text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    const handleEvent = (rawEvent) => {
        let eventType = 'message';
        let data = '';

        for (const line of rawEvent.split('\n')) {
            if (line.startsWith('event:')) eventType = line.slice(6).trim();
            else if (line.startsWith('data:')) data += line.slice(5).trim();
        }

        if (!data || data === '[DONE]') return;

        let parsed;
        try {
            parsed = JSON.parse(data);
        } catch (e) {
            return;
        }

        if (eventType === 'message_complete') {
            completed = true;
            console.info('[stream] message_complete', parsed);
            if (onComplete) onComplete(parsed);
            return;
        }

        if (parsed && parsed.error) {
            errored = true;
            console.warn('[stream] error event', parsed.error);
            if (onError) onError(parsed.error);
            return;
        }

        if (parsed && typeof parsed.content === 'string' && parsed.content) {
            chunksCount += 1;
            if (chunksCount === 1) console.info('[stream] first chunk');
            if (onChunk) onChunk(parsed.content);
        }
    };

    const processRaw = (rawText) => {
        if (!rawText) return;
        buffer += normalize(rawText);

        let idx;
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
            const rawEvent = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            handleEvent(rawEvent);
        }
    };

    const flush = () => {
        if (buffer.trim()) {
            handleEvent(buffer);
            buffer = '';
        }
    };

    const finished = () => ({ completed, errored, chunksCount });

    return { processRaw, flush, finished };
}

export const messageService = {
    // History of messages in a chat
    async getChatMessages(chatId) {
        const response = await apiClient.get(`/chats/${chatId}/messages/`);
        return response.data;
    },

    // Streaming generation (SSE) via fetch + ReadableStream.
    // Handlers: { onChunk(text), onComplete(message), onError(text) }
    async createAssistantMessageStream(chatId, payload, { onChunk, onComplete, onError } = {}) {
        const processor = createSseProcessor({ onChunk, onComplete, onError });

        const response = await fetchWithAuth(
            `/api/v1/chats/${chatId}/messages/text/stream`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Accept: 'text/event-stream',
                },
                credentials: 'include',
                body: JSON.stringify(payload),
            }
        );

        if (!response.ok) {
            let detail = `Request failed (${response.status})`;
            try {
                const body = await response.json();
                if (body && body.detail) detail = body.detail;
            } catch (e) { /* ignore */ }
            console.error('[stream] http error', detail);
            if (onError) onError(detail);
            throw new Error(detail);
        }

        if (!response.body) throw new Error('ReadableStream not supported');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;

        while (!done) {
            const result = await reader.read();
            done = result.done;
            if (!done) {
                processor.processRaw(decoder.decode(result.value, { stream: true }));
            }
        }

        // Flush any remaining partial event
        processor.flush();

        // Diagnostic: if the stream ended without content/completion/error,
        // let the UI know explicitly (should not happen normally).
        const { completed, errored, chunksCount } = processor.finished();
        if (!completed && !errored && chunksCount === 0) {
            console.warn('[stream] ended without any events');
            if (onError) onError('Stream finished without any data');
        }
    },
};