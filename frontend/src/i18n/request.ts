import { cookies, headers } from "next/headers";

const locales = ["en", "fr"] as const;
export type Locale = (typeof locales)[number];

export function isValidLocale(value: string): value is Locale {
  return locales.includes(value as Locale);
}

/** Get preferred locale from cookie, then Accept-Language header. Used from server components. */
export async function getLocale(): Promise<Locale> {
  const cookieStore = await cookies();
  const cookieLocale = cookieStore.get("locale")?.value;
  if (cookieLocale && isValidLocale(cookieLocale)) return cookieLocale;
  const headersList = await headers();
  const acceptLanguage = headersList.get("accept-language") ?? "";
  const preferred = acceptLanguage
    .split(",")
    .map((s) => s.split(";")[0].trim().slice(0, 2).toLowerCase())
    .find((lang) => isValidLocale(lang));
  return preferred ?? "en";
}
