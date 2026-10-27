import Image from 'next/image';

/** Wide illustrated header for the learner pages: title on the left, AI Coach artwork on the right. */
export default function PageBanner({
  image, title, sub, eyebrow, children, heading: Heading = 'h1', priority = false, className = '',
}: {
  image: string;
  title?: string;
  sub?: React.ReactNode;
  eyebrow?: React.ReactNode;
  children?: React.ReactNode;
  heading?: 'h1' | 'h2';
  priority?: boolean;
  className?: string;
}) {
  return (
    <section className={`page-banner${title ? '' : ' page-banner-art'} ${className}`.trim()} aria-hidden={title ? undefined : true}>
      <div className="page-banner-media">
        <Image src={`/img/${image}.webp`} alt="" fill priority={priority} sizes="(max-width: 700px) 100vw, 1100px" />
      </div>
      {title && (
        <div className="page-banner-text">
          {eyebrow && <span className="page-banner-eyebrow">{eyebrow}</span>}
          <Heading>{title}</Heading>
          {sub && <p>{sub}</p>}
          {children && <div className="page-banner-extra">{children}</div>}
        </div>
      )}
    </section>
  );
}
