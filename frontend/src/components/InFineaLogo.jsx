import React from "react";

/**
 * InFinea Brand Logo — uses the actual brand logo PNG with transparent background.
 *
 * Usage:
 *   <InFineaLogo size={32} />
 *   <InFineaLogo size={48} withText />
 *   <InFineaLogo size={24} variant="light" />
 */
export default function InFineaLogo({ size = 32, withText = false, variant = "default", className = "", animate = false }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <img
        src="/logo-infinea.png"
        alt="InFinea"
        width={size}
        height={size}
        className={`flex-shrink-0 object-contain ${animate ? "animate-[spin_30s_linear_infinite]" : ""}`}
        style={{
          width: size,
          height: size,
          filter: "drop-shadow(0 1px 2px rgba(69, 148, 146, 0.15))",
        }}
      />

      {withText && (
        <span
          className="font-sans font-semibold tracking-tight font-bold tracking-tight leading-none"
          style={{
            fontSize: size * 0.5,
            background: variant === "light"
              ? "linear-gradient(135deg, #FFFFFF, #D0E8E6)"
              : "linear-gradient(135deg, #275255 20%, #459492 80%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          InFinea
        </span>
      )}
    </div>
  );
}
