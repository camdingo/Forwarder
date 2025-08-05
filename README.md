Need to forward data across different machines to support legacy executables and 

There is a listen server that we can connect to, but need to distribute the load off of that machine to preseve bandwidth and move the connection management to a different network


Per each connection to forward as defined in the ini file
We will start a thread that
 - connects to the remote server
 - starts a thread to receive remote data, and broadcast to clients
 - opens a listen server
 - accepts incoming connections and adds to client list

