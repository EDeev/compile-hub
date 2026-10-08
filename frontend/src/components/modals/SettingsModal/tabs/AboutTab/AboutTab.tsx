import { useLanguagesStore } from "@/store/languagesStore"
import { useT } from "@/i18n"
import styles from "./AboutTab.module.css"

export const AboutTab = () => {
  const t = useT()
  const languages = useLanguagesStore((s) => s.languages)
  return (
    <div className={styles.mainContainer}>
      <h2 className='settingsTitle'>{t("settings.aboutTitle")}</h2>
      <p>{t("settings.aboutText")}</p>
      <p>{t("settings.languages")}:</p>
      <ul>
        {languages.map((lang) => (
          <li key={lang.id}>
            {lang.name}
            {lang.version ? ` ${lang.version}` : ""}
            {!lang.enabled ? " —" : ""}
          </li>
        ))}
      </ul>
      <p>{t("settings.authors")}:</p>
      <ul>
        <li>
          <a
            className='link'
            href='https://github.com/PetrSaprykin'
            target='_blank'
            rel='noreferrer'
          >
            Petr Saprykin
          </a>{" "}
          — {t("settings.design")}
        </li>
        <li>
          <a
            className='link'
            href='https://github.com/EDeev'
            target='_blank'
            rel='noreferrer'
          >
            Egor Deev
          </a>{" "}
          — {t("settings.backend")}
        </li>
      </ul>
    </div>
  )
}
