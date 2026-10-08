import { createElement } from "react"
import cppIcon from "@/assets/icons/cpp.svg"
import pythonIcon from "@/assets/icons/python.svg"
import javaIcon from "@/assets/icons/java.svg"
import jsIcon from "@/assets/icons/js.svg"
import goIcon from "@/assets/icons/go.svg"
import folderIcon from "@/assets/icons/folder.png"

export const Icons = {
  cppIcon,
  pythonIcon,
  javaIcon,
  jsIcon,
  goIcon,
  folderIcon
} as const

const BY_EXTENSION: Record<string, string> = {
  py: pythonIcon,
  go: goIcon,
  java: javaIcon,
  cpp: cppIcon,
  cc: cppIcon,
  cxx: cppIcon,
  c: cppIcon,
  js: jsIcon
}

/** Иконка файла по расширению. */
export const fileIcon = (ext: string) =>
  BY_EXTENSION[ext] ? createElement("img", { src: BY_EXTENSION[ext] }) : null
