export const timeAgo = (isoDate: string): string => {
  const now = new Date()
  const past = new Date(isoDate)
  const diffMs = now.getTime() - past.getTime()

  if (diffMs < 0) return "в будущем"

  const seconds = Math.floor(diffMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  const weeks = Math.floor(days / 7)
  const months = Math.floor(days / 30)
  const years = Math.floor(days / 365)

  /* prettier-ignore */

  /* -----В БУДУЩЕМ БУДЕТ ПЕРЕКЛЮЧАТЕЛЬ ЯЗЫКОВ----- */

  // для английского языка
  if (seconds < 60)
  return `${seconds} ${pluralizeEng(seconds, "second")} ago`
  if (minutes < 60) return `${minutes} ${pluralizeEng(minutes, "minute")} ago`
  if (hours < 24) return `${hours} ${pluralizeEng(hours, "hour")} ago`
  if (days < 7) return `${days} ${pluralizeEng(days, "day")} ago`
  if (weeks < 5) return `${weeks} ${pluralizeEng(weeks, "week")} ago`
  if (months < 12) return `${months} ${pluralizeEng(months, "month")} ago`
  return `${years} ${pluralizeEng(years, "year")} ago`

  // для русского языка
  if (seconds < 60)
    return `${seconds} ${pluralizeRus(seconds, "секунда", "секунды", "секунд")} назад`
  if (minutes < 60) return `${minutes} ${pluralizeRus(minutes, "минута", "минуты", "минут")} назад`
  if (hours < 24) return `${hours} ${pluralizeRus(hours, "час", "часа", "часов")} назад`
  if (days < 7) return `${days} ${pluralizeRus(days, "день", "дня", "дней")} назад`
  if (weeks < 5) return `${weeks} ${pluralizeRus(weeks, "неделя", "недели", "недель")} назад`
  if (months < 12) return `${months} ${pluralizeRus(months, "месяц", "месяца", "месяцев")} назад`
  return `${years} ${pluralizeRus(years, "год", "года", "лет")} назад`
}

// склонение слов по числам для английского языка
function pluralizeEng(count: number, singular: string): string {
  return count === 1 ? singular : singular + "s"
}

// склонение слов по числам для русского языка
function pluralizeRus(number: number, one: string, few: string, many: string): string {
  const n = Math.abs(number) % 100 // на всякий случай
  const n1 = n % 10
  if (n > 10 && n < 20) return many
  if (n1 > 1 && n1 < 5) return few
  if (n1 === 1) return one
  return many
}
