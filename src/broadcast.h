/*
 * UniFi controllable switch - broadcast sender (header)
 */
#ifndef __BROADCAST_H__
#define __BROADCAST_H__

int broadcast(const unsigned short int port, const void *data, size_t len);

#endif /* __BROADCAST_H__ */
