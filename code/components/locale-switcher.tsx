'use client';

import { usePathname, useRouter } from '@/i18n/navigation';
import { useLocale } from 'next-intl';

export default function LocaleSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const switchLocale = (newLocale: string) => {
    if (newLocale !== locale) {
      router.replace(pathname, { locale: newLocale });
      router.refresh();
    }
  };

  return (
    <select
      className="w-16 h-8 text-sm font-semibold flex justify-between gap-1 border-2 hover:bg-secondary/50"
      value={locale}
      onChange={e => switchLocale(e.target.value)}>
      <option value="en">EN</option>
      <option value="ms">MS</option>
    </select>
  );
}