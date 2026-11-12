import type { JSX } from "react";
import { BrandMark } from "@/components/brand/BrandMark";
import styles from "./WelcomeTransition.module.css";

interface WelcomeTransitionProps {
  organizationName: string;
}

export function WelcomeTransition({ organizationName }: WelcomeTransitionProps): JSX.Element {
  return (
    <div className={styles.overlay} role="status" aria-live="polite">
      <div className={styles.welcome}>
        <div className={styles.markWrap}><BrandMark size="large" className={styles.mark} /></div>
        <p className={styles.wordmark}>Chatrio</p>
        <h1>Welcome to {organizationName}.</h1>
        <p className={styles.caption}>Getting your workspace ready</p>
        <span className={styles.progress} aria-hidden="true"><span /></span>
      </div>
    </div>
  );
}
