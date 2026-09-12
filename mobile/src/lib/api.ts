import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  LoginResponse,
  ListResponse,
  Member,
  PortalData,
  Prayer,
  User,
} from './types';

export const STORAGE = {
  serverUrl: 'fbmi:server_url',
  token: 'fbmi:token',
  user: 'fbmi:user',
  member: 'fbmi:member',
};

export const DEFAULT_SERVER_URL = 'https://fbministry.org';

export async function getServerUrl(): Promise<string> {
  try {
    const v = await AsyncStorage.getItem(STORAGE.serverUrl);
    return v && v.trim() ? v.trim().replace(/\/+$/, '') : DEFAULT_SERVER_URL;
  } catch {
    return DEFAULT_SERVER_URL;
  }
}

export async function setServerUrl(url: string): Promise<void> {
  const clean = url.trim().replace(/\/+$/, '');
  await AsyncStorage.setItem(STORAGE.serverUrl, clean);
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(
  path: string,
  opts: { method?: string; token?: string | null; json?: unknown; form?: FormData } = {},
): Promise<T> {
  const base = await getServerUrl();
  const url = `${base}/api/${path}`;
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;
  if (opts.json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(opts.json);
  } else if (opts.form) {
    body = opts.form;
  }
  if (opts.token) {
    headers.Authorization = `Token ${opts.token}`;
  }
  let res: Response;
  try {
    res = await fetch(url, { method: opts.method || 'GET', headers, body });
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your connection.');
  }
  const text = await res.text();
  let data: Record<string, unknown> | null = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }
  if (!res.ok) {
    const message = data && typeof data.error === 'string' ? data.error : `Request failed (${res.status})`;
    throw new ApiError(res.status, message);
  }
  return (data ?? {}) as T;
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>('login/', { method: 'POST', json: { username, password } }),

  logout: (token: string) => request<{ ok: boolean }>('logout/', { method: 'POST', token }),

  me: (token: string) => request<{ user: User; member: Member | null }>('me/', { token }),

  portal: (token: string) => request<PortalData>('portal/', { token }),

  updateProfile: (token: string, fields: Record<string, string>) =>
    request<{ ok: boolean; user: User; member: Member | null }>('profile/', {
      method: 'POST',
      token,
      json: fields,
    }),

  uploadPhoto: async (token: string, photo: { uri: string; name: string; type: string }) => {
    const base = await getServerUrl();
    const form = new FormData();
    form.append('photo', { uri: photo.uri, name: photo.name, type: photo.type } as unknown as Blob);
    const headers: Record<string, string> = { Authorization: `Token ${token}` };
    const res = await fetch(`${base}/api/profile/`, { method: 'POST', headers, body: form });
    const text = await res.text();
    let data: Record<string, unknown> | null = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = null;
      }
    }
    if (!res.ok) {
      const message = data && typeof data.error === 'string' ? data.error : `Upload failed (${res.status})`;
      throw new ApiError(res.status, message);
    }
    return (data ?? {}) as { ok: boolean; user: User; member: Member | null };
  },

  changePassword: (token: string, oldPassword: string, newPassword: string) =>
    request<{ ok: boolean }>('profile/password/', {
      method: 'POST',
      token,
      json: { old_password: oldPassword, new_password: newPassword },
    }),

  list: <T>(token: string, endpoint: string) => request<ListResponse<T>>(endpoint, { token }),

  registerEvent: (token: string, eventId: number) =>
    request<{ ok: boolean; registered: boolean }>(`events/${eventId}/register/`, { method: 'POST', token }),

  createPrayer: (token: string, data: { title: string; request: string; category: string; is_confidential: boolean }) =>
    request<{ ok: boolean; prayer: Prayer }>('prayers/', { method: 'POST', token, json: data }),
};

export const ENDPOINTS: Record<string, string> = {
  groups: 'groups/',
  givings: 'givings/',
  attendance: 'attendance/',
  events: 'events/',
  announcements: 'announcements/',
  sermons: 'sermons/',
  prayers: 'prayers/',
};