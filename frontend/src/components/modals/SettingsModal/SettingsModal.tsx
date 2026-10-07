import { useState } from "react"
import { GeneralTab } from "./tabs/GeneralTab/GeneralTab"
import { EditorTab } from "./tabs/EditorTab/EditorTab"
import styles from "./SettingsModal.module.css"
import { AboutTab } from "./tabs/AboutTab/AboutTab"

type TabType = "profile" | "editor" | "appearance" | "about"

export const SettingsModal = () => {
  const [activeTab, setActiveTab] = useState<TabType>("profile")

  return (
    <div className={styles.main}>
      {/* Боковая панель с вкладками */}
      <div className={styles.tabPanel}>
        <button
          onClick={() => setActiveTab("profile")}
          className={`${styles.tabButton} ${activeTab === "profile" ? styles.isActive : ""}`}
        >
          General
        </button>
        <button
          onClick={() => setActiveTab("editor")}
          className={`${styles.tabButton} ${activeTab === "editor" ? styles.isActive : ""}`}
        >
          Editor
        </button>
        <button
          onClick={() => setActiveTab("appearance")}
          className={`${styles.tabButton} ${activeTab === "appearance" ? styles.isActive : ""}`}
        >
          Appereance
        </button>
        <button
          onClick={() => setActiveTab("about")}
          className={`${styles.tabButton} ${activeTab === "about" ? styles.isActive : ""}`}
        >
          About
        </button>
      </div>

      {/* Контент вкладки */}
      <div className={styles.tabContent}>
        {activeTab === "profile" && <GeneralTab />}
        {activeTab === "editor" && <EditorTab />}
        {activeTab === "appearance" && <AppearanceTab />}
        {activeTab === "about" && <AboutTab />}
      </div>
    </div>
  )
}

const AppearanceTab = () => (
  <div>
    <h3 className='text-lg font-medium mb-4'>Appereance</h3>
    <div className='space-y-4'>
      <p>There will be some options..</p>
    </div>
  </div>
)
