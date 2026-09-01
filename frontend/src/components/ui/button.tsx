import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-xs font-semibold ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-white text-zinc-950 shadow-sm hover:bg-zinc-200 active:scale-[0.98]",
        destructive:
          "bg-rose-500/15 text-rose-400 border border-rose-500/30 hover:bg-rose-500 hover:text-white",
        outline:
          "border border-white/10 bg-white/[0.03] hover:bg-white/[0.08] hover:text-white hover:border-white/20 text-zinc-300",
        secondary:
          "bg-zinc-800/80 text-zinc-100 hover:bg-zinc-700/80 border border-zinc-700/50",
        ghost:
          "hover:bg-white/10 hover:text-white text-zinc-400",
        link:
          "text-violet-400 underline-offset-4 hover:underline",
        gradient:
          "bg-gradient-to-r from-violet-600 via-indigo-600 to-indigo-700 text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-indigo-600 hover:shadow-violet-500/30 active:scale-[0.98]",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-11 rounded-xl px-6 text-sm",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
