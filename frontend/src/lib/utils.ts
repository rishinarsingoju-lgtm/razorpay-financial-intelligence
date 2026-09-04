import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatINR(value: number): string {
  return new Intl.NumberFormat("en-IN", { currency: "INR", maximumFractionDigits: 2, minimumFractionDigits: 2, style: "currency" }).format(value);
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`));
}
