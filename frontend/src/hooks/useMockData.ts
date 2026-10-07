import { type Item } from "@/types/fileSystem"

export const useMockData = () => {
  /* prettier-ignore */
  const itemsArray: Item[] = [
    // Папки
    { id: 0, name: "frontend", type: "folder", size: "45mb", modified: "2025-07-03T12:00:00.000Z" },       // 1 day ago
    { id: 1, name: "backend", type: "folder", size: "67mb", modified: "2025-07-04T10:00:00.000Z" },        // 2 hours ago
    { id: 2, name: "algorithms", type: "folder", size: "23mb", modified: "2025-07-01T12:00:00.000Z" },     // 3 days ago
    { id: 3, name: "practice", type: "folder", size: "34mb", modified: "2025-06-27T12:00:00.000Z" },       // 1 week ago
    { id: 4, name: "archive", type: "folder", size: "89mb", modified: "2025-06-20T12:00:00.000Z" },        // 2 weeks ago

    // Файлы в корне
    { id: 10, name: "main.py", type: "file", folder: null, size: "2.3kb", modified: "2025-07-04T11:00:00.000Z"  },     // 1 hour ago
    { id: 11, name: "config.js", type: "file", folder: null, size: "1.8kb", modified: "2025-07-04T10:00:00.000Z" },   // 2 hours ago
    { id: 12, name: "utils.go", type: "file", folder: null, size: "4.5kb", modified: "2025-07-03T12:00:00.000Z" },    // 1 day ago
    { id: 13, name: "helper.cpp", type: "file", folder: null, size: "3.2kb", modified: "2025-07-01T12:00:00.000Z" },  // 3 days ago

    // Файлы в папке frontend (id: 0)
    { id: 14, name: "App.js", type: "file", folder: 0, size: "8.5kb", modified: "2025-07-04T11:30:00.000Z" },         // 30 minutes ago
    { id: 15, name: "index.js", type: "file", folder: 0, size: "1.2kb", modified: "2025-07-04T11:00:00.000Z" },       // 1 hour ago
    { id: 16, name: "components.js", type: "file", folder: 0, size: "15kb", modified: "2025-07-04T10:00:00.000Z" },   // 2 hours ago
    { id: 17, name: "hooks.js", type: "file", folder: 0, size: "6.7kb", modified: "2025-07-03T12:00:00.000Z" },       // 1 day ago

    // Файлы в папке backend (id: 1)
    { id: 20, name: "server.py", type: "file", folder: 1, size: "12kb", modified: "2025-07-04T11:15:00.000Z" },        // 45 minutes ago
    { id: 21, name: "database.py", type: "file", folder: 1, size: "9.8kb", modified: "2025-07-04T11:00:00.000Z" },     // 1 hour ago
    { id: 22, name: "auth.py", type: "file", folder: 1, size: "7.2kb", modified: "2025-07-04T10:00:00.000Z" },         // 2 hours ago
    { id: 23, name: "models.py", type: "file", folder: 1, size: "14kb", modified: "2025-07-03T12:00:00.000Z" },         // 1 day ago

    // Файлы в папке algorithms (id: 2)
    { id: 27, name: "sorting.cpp", type: "file", folder: 2, size: "6.4kb", modified: "2025-07-04T10:00:00.000Z" },      // 2 hours ago
    { id: 28, name: "binary_search.py", type: "file", folder: 2, size: "2.8kb", modified: "2025-07-03T12:00:00.000Z" }, // 1 day ago
    { id: 29, name: "graph_traversal.java", type: "file", folder: 2, size: "9.7kb", modified: "2025-07-02T12:00:00.000Z" }, // 2 days ago
    { id: 30, name: "dynamic_programming.cpp", type: "file", folder: 2, size: "7.3kb", modified: "2025-07-01T12:00:00.000Z" }, // 3 days ago

    // Файлы в папке practice (id: 3)
    { id: 33, name: "exercise_1.py", type: "file", folder: 3, size: "1.8kb", modified: "2025-07-04T09:00:00.000Z" },      // 3 hours ago
    { id: 34, name: "exercise_2.js", type: "file", folder: 3, size: "2.1kb", modified: "2025-07-03T12:00:00.000Z" },       // 1 day ago
    { id: 35, name: "homework.cpp", type: "file", folder: 3, size: "3.4kb", modified: "2025-07-02T12:00:00.000Z" },        // 2 days ago
    { id: 36, name: "lab_work.java", type: "file", folder: 3, size: "5.7kb", modified: "2025-07-01T12:00:00.000Z" },       // 3 days ago

    // Файлы в папке archive (id: 4)
    { id: 40, name: "old_project.js", type: "file", folder: 4, size: "25kb", modified: "2025-06-04T12:00:00.000Z" },       // 1 month ago
    { id: 41, name: "legacy_server.py", type: "file", folder: 4, size: "18kb", modified: "2025-05-04T12:00:00.000Z" },    // 2 months ago
    { id: 42, name: "deprecated_api.cpp", type: "file", folder: 4, size: "12kb", modified: "2025-04-04T12:00:00.000Z" },  // 3 months ago

    // Файлы в корневой директории
    { id: 43, name: "exercise_1.py", type: "file", folder: null, size: "1.8kb", modified: "2025-07-04T09:00:00.000Z" },    // 3 hours ago
    { id: 44, name: "exercise_2.js", type: "file", folder: null, size: "2.1kb", modified: "2025-07-03T12:00:00.000Z"},     // 1 day ago
    { id: 45, name: "homework.cpp", type: "file", folder: null, size: "3.4kb", modified: "2025-07-02T12:00:00.000Z" },      // 2 days ago
    { id: 46, name: "lab_work.java", type: "file", folder: null, size: "5.7kb", modified: "2025-07-01T12:00:00.000Z" },     // 3 days ago
    { id: 47, name: "exercise_1.py", type: "file", folder: null, size: "1.8kb", modified: "2025-07-04T09:00:00.000Z" },    // 3 hours ago
    { id: 48, name: "exercise_2.js", type: "file", folder: null, size: "2.1kb", modified: "2025-07-03T12:00:00.000Z" },     // 1 day ago
    { id: 49, name: "homework.cpp", type: "file", folder: null, size: "3.4kb", modified: "2025-07-02T12:00:00.000Z" },      // 2 days ago
    { id: 50, name: "lab_work.java", type: "file", folder: null, size: "5.7kb", modified: "2025-07-01T12:00:00.000Z" },     // 3 days ago
  ]

  return { itemsArray }
}
