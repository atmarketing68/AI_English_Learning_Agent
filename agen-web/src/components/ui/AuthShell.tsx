import Image from 'next/image';

const WIDTH = { sm: 460, md: 540, lg: 700 } as const;

/** Full-page AI Coach artwork behind a frosted-glass panel: used by sign-in, sign-up and onboarding. */
export default function AuthShell({
  image, title, text, size = 'sm', children,
}: {
  image: string;
  title: string;
  text: string;
  size?: keyof typeof WIDTH;
  children: React.ReactNode;
}) {
  return (
    <main className="auth-page">
      <div className="auth-bg" aria-hidden="true">
        <div className="auth-bg-art">
          <Image key={image} src={`/img/${image}.webp`} alt="" fill priority sizes="100vw" />
        </div>
      </div>
      <div className="auth-caption" aria-hidden="true">
        <h2>{title}</h2>
        <p>{text}</p>
      </div>
      <div className="auth-panel">
        <div className="auth-glass" style={{ maxWidth: WIDTH[size] }}>{children}</div>
      </div>
    </main>
  );
}
