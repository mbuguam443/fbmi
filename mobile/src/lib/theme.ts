export const Colors = {
  bg: '#F6F4EF',
  card: '#FFFFFF',
  navy: '#13294B',
  navyDark: '#0C1D36',
  gold: '#C9A227',
  goldLight: '#F6EDD2',
  text: '#1B2A3A',
  muted: '#6B7684',
  border: '#E5E1D8',
  danger: '#B23B3B',
  success: '#2E7D32',
  info: '#335AA6',
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