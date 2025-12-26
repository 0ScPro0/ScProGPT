export function SVGIcon({ src, width, height, size, children, ...props }) {
  return (
    <div
      {...props}
      style={{
            width: width || size,
            height: height || size,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center'
      }}
      dangerouslySetInnerHTML={{ __html: src }}
    />
  );
}