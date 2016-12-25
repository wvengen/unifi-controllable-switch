/*
 * UniFi controllable switch - broadcast sender
 */
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/udp.h>
#include <unistd.h>
#include <string.h>

int broadcast(const unsigned short int port, const void *data, size_t len) {
  int fd = socket(PF_INET, SOCK_DGRAM, 0);
  if (fd < 0) return 1;

  const int enable = 1;
  if (setsockopt(fd, SOL_SOCKET, SO_BROADCAST, &enable, sizeof(enable))) goto error_close;

  struct sockaddr_in addr;
  memset(&addr, 0, sizeof(addr));
  addr.sin_family = AF_INET;
  addr.sin_addr.s_addr = htonl(INADDR_BROADCAST);
  addr.sin_port = htons(port);

  if (sendto(fd, data, len, 0, (struct sockaddr*)&addr, sizeof(addr)) < 0) goto error_close;

  close(fd);
  return 0;

error_close:
  close(fd);
  return 1;
}
