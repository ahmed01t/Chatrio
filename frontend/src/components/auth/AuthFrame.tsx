import type { JSX, ReactNode } from "react";
import { Instagram, MessageCircle, PackageSearch } from "lucide-react";
import { BrandMark } from "@/components/brand/BrandMark";
import styles from "./AuthFrame.module.css";

interface AuthFrameProps {
  children: ReactNode;
}

export function AuthFrame({ children }: AuthFrameProps): JSX.Element {
  return (
    <main className={styles.authCanvas}>
      <div className={styles.layout}>
        <aside className={styles.story} aria-label="Chatrio product preview">
          <div className={styles.brand}>
            <BrandMark size="large" />
            <span>Chatrio</span>
          </div>

          <div className={styles.storyCopy}>
            <p className={styles.storyTitle}>Every chat has a next step.</p>
            <p className={styles.storyDescription}>Connect customer messages with your catalog, orders, and team.</p>
          </div>

          <div className={styles.preview}>
            <p className={styles.previewLabel}>Example conversation</p>
            <div className={styles.channels} role="list" aria-label="Supported message channels">
              <span data-channel="whatsapp" role="listitem"><MessageCircle size={14} />WhatsApp</span>
              <span data-channel="instagram" role="listitem"><Instagram size={14} />Instagram</span>
            </div>
            <div className={styles.customerMessage}>Do you have the espresso blend today?</div>
            <div className={styles.assistantMessage}>I’ll check the current catalog for you.</div>
            <div className={styles.previewRule} />
            <div className={styles.previewFooter}>
              <span className={styles.catalogIcon}><PackageSearch size={19} /></span>
              <span><strong>Catalog checked first</strong><small>Products and orders stay connected.</small></span>
            </div>
          </div>

          <p className={styles.storyFoot}>One workspace for the conversations behind your store.</p>
        </aside>

        <section className={styles.formSide} aria-label="Merchant account">
          <div className={styles.mobileBrand}>
            <BrandMark size="medium" />
            <span>Chatrio</span>
          </div>
          {children}
        </section>
      </div>
    </main>
  );
}
