export const Platform = {
  OS: 'android' as const,
  select: (obj: any) => obj.android ?? obj.default,
};

export default {
  Platform,
};
