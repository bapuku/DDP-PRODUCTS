import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { isValidLocale } from "@/i18n/request";

const LOCALE_COOKIE = "locale";
const DEFAULT_LOCALE = "en";

export function middleware(request: NextRequest) {
  const existing = request.cookies.get(LOCALE_COOKIE)?.value;
  if (existing && isValidLocale(existing)) {
    return NextResponse.next();
  }
  const acceptLanguage = request.headers.get("accept-language") ?? "";
  const preferred = acceptLanguage
    .split(",")
    .map((s) => s.split(";")[0].trim().slice(0, 2).toLowerCase())
    .find((lang) => isValidLocale(lang));
  const locale = preferred ?? DEFAULT_LOCALE;
  const response = NextResponse.next();
  response.cookies.set(LOCALE_COOKIE, locale, { path: "/", maxAge: 60 * 60 * 24 * 365 });
  return response;
}

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
