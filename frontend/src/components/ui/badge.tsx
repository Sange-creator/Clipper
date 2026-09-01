import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-white text-zinc-950 shadow hover:bg-zinc-200",
        secondary:
          "border-white/10 bg-white/[0.04] text-zinc-300 hover:bg-white/[0.08]",
        destructive:
          "border-rose-500/20 bg-rose-500/10 text-rose-400",
        outline:
          "border-white/15 text-zinc-300",
        success:
          "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
        brand:
          "border-violet-500/25 bg-violet-500/10 text-violet-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
