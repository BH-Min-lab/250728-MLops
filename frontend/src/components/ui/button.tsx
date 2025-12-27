import { cn } from "../../lib/utils";
import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> { }

export const Button = ({ className, ...props }: ButtonProps) => {
    return (
        <button
            className={cn(
                "px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600",
                className
            )}
            {...props}
        />
    );
};
