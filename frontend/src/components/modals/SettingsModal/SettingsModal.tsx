import { useState } from "react"
import { GeneralTab } from "./tabs/GeneralTab/GeneralTab"
import { EditorTab } from "./tabs/EditorTab/EditorTab"
import { AboutTab } from "./tabs/AboutTab/AboutTab"
import { useT, type MessageKey } from "@/i18n"
import styles from "./SettingsModal.module.css"

type TabType = "general" | "editor" | "about"

const TABS: [TabType, MessageKey][] = [
  ["general", "settings.general"],
  ["editor", "settings.editor"],
  ["about", "settings.about"]
]

export const SettingsModal = () => {
  const t = useT()
  const [activeTab, setActiveTab] = useState<TabType>("general")

  return (
    <div className={styles.main}>
      <div className={styles.tabPanel}>
        {TABS.map(([tab, label]) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`${styles.tabButton} ${activeTab === tab ? styles.isActive : ""}`}
          >
            {t(label)}
          </button>
        ))}
      </div>
      <div className={styles.tabContent}>
        {activeTab === "general" && <GeneralTab />}
        {activeTab === "editor" && <EditorTab />}
        {activeTab === "about" && <AboutTab />}
      </div>
    </div>
  )
}
