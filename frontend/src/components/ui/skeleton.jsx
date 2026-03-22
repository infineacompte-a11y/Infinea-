import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}) {
  return (
    <div
      className={cn("animate-pulse rounded-xl bg-gradient-to-r from-[#459492]/[0.06] via-[#459492]/[0.12] to-[#459492]/[0.06] bg-[length:200%_100%] animate-shimmer", className)}
      {...props} />
  );
}

export { Skeleton }
