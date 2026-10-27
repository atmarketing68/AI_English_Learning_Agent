import Image from 'next/image';

/** Two-column frame for the sign-in / sign-up / onboarding pages: AI Coach artwork beside the form. */
export default function AuthShell({
  image, title, text, children,
}: {
  image: string;
  title: string;
  text: string;
  children: React.ReactNode;
}) {
  return (
    <main className="auth-split">
      <aside className="auth-art" aria-hidden="true">
        <Image key={image} src={`/img/${image}.webp`} alt="" fill priority sizes="(max-width: 900px) 100vw, 55vw" />
        <div className="auth-art-text">
          <h2>{title}</h2>
          <p>{text}</p>
        </div>
      </aside>
      <div className="auth-panel">{children}</div>
    </main>
  );
}
