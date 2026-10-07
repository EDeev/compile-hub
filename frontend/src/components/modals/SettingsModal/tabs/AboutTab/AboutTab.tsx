import styles from "./AboutTab.module.css"

export const AboutTab = () => {
  return (
    <div className={styles.mainContainer}>
      <h3>About us</h3>
      <p>
        CompileHub - it's a simple and easy way to compile your code using
        web-browser (отредачить)
      </p>
      <p>Supported languages:</p>
      <ul>
        <li>Python</li>
        <li>Java</li>
        <li>Golang</li>
        <li>JavaScript</li>
        <li>C++</li>
      </ul>
      <p>Authors: Petr Saprykin, Egor Deev</p>
    </div>
  )
}
