import { createLink, type LinkComponent } from "@tanstack/react-router";
import type { VariantProps } from "class-variance-authority";
import { type ComponentProps, forwardRef } from "react";
import { buttonVariants } from "#/components/ui/button";
import { cn } from "#/lib/utils";

type ButtonAnchorProps = ComponentProps<"a"> & VariantProps<typeof buttonVariants>;

// A link that looks like a Button. It renders a plain <a> with the button's
// styles rather than Base UI's Button, which would add role="button": links
// should stay links for screen readers, middle-click and "open in new tab".
const ButtonAnchor = forwardRef<HTMLAnchorElement, ButtonAnchorProps>(function ButtonAnchor(
  { variant, size, className, ...props },
  ref,
) {
  return <a ref={ref} data-slot="button" className={cn(buttonVariants({ variant, size }), className)} {...props} />;
});

const CreatedButtonLink = createLink(ButtonAnchor);

/** A type-safe router link styled as a Button. */
export const ButtonLink: LinkComponent<typeof ButtonAnchor> = (props) => (
  <CreatedButtonLink preload="intent" {...props} />
);
