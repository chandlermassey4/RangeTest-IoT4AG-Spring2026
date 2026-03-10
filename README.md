# RangeTest-IoT4AG-Spring2026

This range test operates using the dect_shell sample. In order to build the project you must use the normal prj.conf file and select the correct board for your applications. No other modifcation to the build should be made.

### Range Test Instructions

1. Flash the sample onto both the client and server board
2. Each board should be connect to seperate computers and one computer should run server.py and another runs client.py (both from the terminal)
3. One should use apple maps to find the coordinates of each locations (recomend one board stay in a single location), and one can estimate the distance until more accurate recording later on.
4. Once each board is connected, the server board should type "ping"
   
    4.1 The server board will say it is ready, and then the client can press enter
   
    4.2 After several seconds the client say will say packets recieved or error.
   
    4.3 Next the server will type "stop" and wait to tell the client to proceed until "stopped" is output in the server terminal. The ping test is now concluded.
   
5. After completion of the ping test, the server can type "perf" to test data throughput

     5.1 Client will press enter to proceed after the server says it is ready.

     5.2 The client will say tell the server to stop and the server should type stop and the test is concluded

6. Continue back to step 3 to continue testing from a new distance.

**Note:** You must specify your output file path at the top of the file.
     
