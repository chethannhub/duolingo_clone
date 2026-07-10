import Image from "next/image";

type IconImageProps = {
  src: string;
  alt: string;
  size?: number;
  className?: string;
  priority?: boolean;
};

export function IconImage({
  src,
  alt,
  size = 32,
  className = "",
  priority = false,
}: IconImageProps) {
  return (
    <Image
      src={src}
      alt={alt}
      width={size}
      height={size}
      priority={priority}
      className={className}
    />
  );
}
