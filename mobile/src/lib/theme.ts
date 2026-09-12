export const Colors = {
  bg: '#F3F6FC',
  card: '#FFFFFF',
  navy: '#0D6EFD',
  navyDark: '#0A56C8',
  navySoft: '#E7EFFE',
  gold: '#C9A227',
  goldLight: '#F7E9C3',
  text: '#17233D',
  muted: '#5B6B85',
  border: '#DEE7F4',
  danger: '#BF2D30',
  success: '#198754',
  info: '#0A56C8',
};

export const Radius = {
  sm: 8,
  md: 12,
  lg: 16,
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
};

export const Shadow = {
  shadowColor: '#000',
  shadowOffset: { width: 0, height: 1 },
  shadowOpacity: 0.06,
  shadowRadius: 3,
  elevation: 2,
};

export function formatDate(iso?: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function formatMoney(amount?: string | number | null): string {
  if (amount === null || amount === undefined || amount === '') return 'KES 0';
  const n = Number(amount);
  if (Number.isNaN(n)) return String(amount);
  const opts = n % 1 === 0 ? { maximumFractionDigits: 0 } : { minimumFractionDigits: 2, maximumFractionDigits: 2 };
  return `KES ${n.toLocaleString('en-KE', opts)}`;
}

export function initials(name?: string | null): string {
  if (!name) return 'FB';
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p.charAt(0).toUpperCase())
    .join('');
}