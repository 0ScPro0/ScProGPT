import styles from './Logo.module.css'
//import logoImage from '../../../assets/images/logo.png';

export function Logo({ onClick }) {
  return (
    <div className={styles.logo}>
      <a href="/" className={styles.link}>
        <span className={styles.text}>ScProGPT</span>
      </a>
    </div>
  );
}