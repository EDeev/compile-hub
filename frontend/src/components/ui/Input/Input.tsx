import { forwardRef, useEffect, useState } from "react"
import styles from "./Input.module.css"
import { CgSpinner } from "react-icons/cg"
import { IoEyeOutline, IoEyeOffOutline } from "react-icons/io5"

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  isRequired?: boolean
  isValidating?: boolean
  icon?: React.ReactNode
  message?: { isValid: boolean; text: string }
  hidePassDeps?: unknown[]
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      icon,
      isRequired: _isRequired = false,
      isValidating = false,
      message,
      hidePassDeps = [],
      type,
      ...props
    },
    ref
  ) => {
    const [showPass, setShowPass] = useState(false)

    const showPassIconProps = {
      onClick: () => setShowPass(!showPass),
      className: styles.showPass
    }

    useEffect(() => {
      setShowPass(false)
      // eslint-disable-next-line react-hooks/exhaustive-deps -- зависимости задаёт вызывающий компонент
    }, hidePassDeps)

    const showPasswordIcon = showPass ? (
      <IoEyeOffOutline {...showPassIconProps} />
    ) : (
      <IoEyeOutline {...showPassIconProps} />
    )
    return (
      <div
        className={`${styles.inputContainer} ${message?.text ? styles.hasNote : ""} ${props?.className}`}
      >
        <div className={styles.inputLine}>
          {icon}
          <input
            ref={ref}
            {...props}
            type={!showPass && type === "password" ? "password" : "text"}
            className={`${isValidating ? styles.isValidating : ""} ${type === "password" ? styles.isPassword : ""}`}
            name={"input"}
          />
          {isValidating && <CgSpinner className={styles.spinner} />}
          {type === "password" && showPasswordIcon}
        </div>
        {message?.text && (
          <p className={styles[message.isValid ? "successNote" : "errorNote"]}>
            {message?.text}
          </p>
        )}
      </div>
    )
  }
)
