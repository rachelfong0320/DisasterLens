
export const DEFAULT_START = "2023-01-01";
export const DEFAULT_END = "2025-12-31";

export const getTimeRange = (range: string) => {
  const now = new Date();
  const currentYear = 2024;
  let start = new Date(DEFAULT_START); 
  let end = new Date(DEFAULT_END);  

  const formatDate = (date: Date) => date.toISOString().split('T')[0];

  switch (range) {
    case "this-week":
      const currentDay = now.getDay() || 7; 
      start = new Date(now.setDate(now.getDate() - currentDay + 1));
      end = new Date();
      break;
    case "last-week":
      const lastWeekEnd = new Date();
      const dayOffset = lastWeekEnd.getDay() || 7;
      lastWeekEnd.setDate(lastWeekEnd.getDate() - dayOffset); // Last Sunday
      const lastWeekStart = new Date(lastWeekEnd);
      lastWeekStart.setDate(lastWeekStart.getDate() - 6); // Last Monday
      return { start: formatDate(lastWeekStart), end: formatDate(lastWeekEnd) };
    case "this-month":
      start = new Date(now.getFullYear(), now.getMonth(), 1);
      end = new Date();
      break;
    case "last-30-days":
      start = new Date(now.setDate(now.getDate() - 30));
      end = new Date();
      break;
    case "this-year":
    default:
      return { 
        start: `${currentYear}-01-01`, 
        end: formatDate(now) 
      };
  }

  return { start: formatDate(start), end: formatDate(end) };
};