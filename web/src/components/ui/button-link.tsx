import { createLink, type LinkComponent } from "@tanstack/react-router";
import { type ComponentProps, forwardRef } from "react";
import { Button } from "#/components/ui/button";

type ButtonAnchorProps = Omit<ComponentProps<typeof Button>, "render" | "nativeButton"> & ComponentProps<"a">;

// A Button that navigates. Base UI needs nativeButton={false} when a button
// renders as <a>, so links keep link semantics instead of fake button ones.
const ButtonAnchor = forwardRef<HTMLAnchorElement, ButtonAnchorProps>(function ButtonAnchor(props, ref) {
  const { variant, size, className, ...anchorProps } = props;
  return (
    <Button variant={variant} size={size} className={className} nativeButton={false} render={<a ref={ref} {...anchorProps} />} />
  );
});

const CreatedButtonLink = createLink(ButtonAnchor);

/** A type-safe router link styled as a Button. */
export const ButtonLink: LinkComponent<typeof ButtonAnchor> = (props) => <CreatedButtonLink preload="intent" {...props} />;
