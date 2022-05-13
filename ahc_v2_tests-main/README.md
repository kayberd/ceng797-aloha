# AdHoc Computing Code Example for Version 2.0.13

In this project, we provided a testing code that you can use for an example to test 
adhoccomputing library with USRP Devices. To test it, you need to use AHC 
Simulator environment. This you can find enviroment link below. As it is mentioned in ahc.yaml part, it uses uhd image so that commincation between USRP devices and adhoccomputing library is provided.

<a href="https://ahc.ceng.metu.edu.tr" target="_blank">Simulation Environment Link</a>
### What is it testing ? 

This testing code test comminication between USRP devices. Currently, USRP devices are mesh connected. When a device broadcast a message, all the devices receive the message. Currently, we have 4 USRP devices that are mesh connected. In future, we are planning to increase it to 10 USRP devices. 

### How to run it ? 

Please click the simulation environment link above and follow instructions. You need to open an account properly and run this code in that simulation environment. 

### Code 

The detailed information about the code is written in test.py file. You can check the command lines in the file. 