import Image from 'next/image';

/** Wide illustration under the headline of the public content pages. */
export default function SeoHeroArt({ name }: { name: string }) {
  return (
    <div className="seo-hero-art" aria-hidden="true">
      <Image src={`/img/${name}.webp`} alt="" fill priority sizes="(max-width: 1000px) 100vw, 980px" />
    </div>
  );
}
