/* ch-rusage FD PROG [ARGS...] — запускает программу пользователя внутри песочницы и пишет в FD её
   собственные пиковый RSS (КБ) и CPU-время (мс): у nsjail rusage общий на всё дерево, включая сам nsjail. */
#include <stdio.h>
#include <stdlib.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 3) return 125;
    int fd = atoi(argv[1]);
    pid_t pid = fork();
    if (pid < 0) return 125;
    if (pid == 0) {
        close(fd);
        execvp(argv[2], argv + 2);
        perror(argv[2]);
        _exit(127);
    }
    int status;
    struct rusage ru;
    if (wait4(pid, &status, 0, &ru) < 0) return 125;
    long cpu_ms = (ru.ru_utime.tv_sec + ru.ru_stime.tv_sec) * 1000L + (ru.ru_utime.tv_usec + ru.ru_stime.tv_usec) / 1000L;
    dprintf(fd, "%ld %ld\n", ru.ru_maxrss, cpu_ms);
    /* в своём pid namespace это init: сигнал себе не доставится — сообщаем о нём кодом 128+N, как nsjail */
    if (WIFSIGNALED(status)) return 128 + WTERMSIG(status);
    return WEXITSTATUS(status);
}
