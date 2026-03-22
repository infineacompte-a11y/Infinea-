import { Toaster as Sonner, toast } from "sonner"

const Toaster = ({
  ...props
}) => {
  return (
    <Sonner
      theme="light"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-white group-[.toaster]:text-[#141E24] group-[.toaster]:border-[#E2E6EA] group-[.toaster]:shadow-lg group-[.toaster]:rounded-xl",
          description: "group-[.toast]:text-[#667085]",
          actionButton:
            "group-[.toast]:bg-[#459492] group-[.toast]:text-white",
          cancelButton:
            "group-[.toast]:bg-[#F8FAFB] group-[.toast]:text-[#667085]",
          success: "group-[.toaster]:border-[#5DB786]/30",
          error: "group-[.toaster]:border-destructive/30",
        },
      }}
      {...props} />
  );
}

export { Toaster, toast }
