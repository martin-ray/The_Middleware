# memory_loading
## on monaka
1. 4GiB : 単位 (GiB/Sec) 
3.53, 3.56, 3.4965, 2.06505, 3.68324 (キャッシュの効果が出てしまっている？)

2. 8GiB : 
3.59551, 3.57622, 3.57622, 3.59066 
3. 16Gib : 
2.98786, 3.34518, 3.54374

4. 32Gib
2.73855, 2.56184, 2.55367, 

### How to turn off cache

## on muffin2


# compression
## single thread (Normal MGARD)
### datasize = 0.0078125GiB
Error tolerance:1e-13
compression ratio: 1.17761
8.38861e+06 bytes -> 7123433 bytes
ThroughPut:8.28561e-10 (GiB/sec)=8.48446e-07 MiB/sec

Error tolerance:1e-12
compression ratio: 1.08292
8.38861e+06 bytes -> 7746281 bytes
ThroughPut:8.30234e-10 (GiB/sec)=8.50159e-07 MiB/sec

Error tolerance:1e-11
compression ratio: 1.05097
8.38861e+06 bytes -> 7981810 bytes
ThroughPut:8.30499e-10 (GiB/sec)=8.50431e-07 MiB/sec

Error tolerance:1e-10
compression ratio: 1.08583
8.38861e+06 bytes -> 7725557 bytes
ThroughPut:8.3094e-10 (GiB/sec)=8.50883e-07 MiB/sec

Error tolerance:1e-09
compression ratio: 1.14625
8.38861e+06 bytes -> 7318288 bytes
ThroughPut:8.28297e-10 (GiB/sec)=8.48176e-07 MiB/sec

Error tolerance:1e-08
compression ratio: 1.33074
8.38861e+06 bytes -> 6303720 bytes
ThroughPut:8.17806e-10 (GiB/sec)=8.37433e-07 MiB/sec

Error tolerance:1e-07
compression ratio: 1.74303
8.38861e+06 bytes -> 4812672 bytes
ThroughPut:8.21417e-10 (GiB/sec)=8.41131e-07 MiB/sec

Error tolerance:1e-06
compression ratio: 2.24316
8.38861e+06 bytes -> 3739643 bytes
ThroughPut:8.26982e-10 (GiB/sec)=8.4683e-07 MiB/sec

Error tolerance:1e-05
compression ratio: 2.99821
8.38861e+06 bytes -> 2797871 bytes
ThroughPut:8.32357e-10 (GiB/sec)=8.52333e-07 MiB/sec

Error tolerance:0.0001
compression ratio: 4.4731
8.38861e+06 bytes -> 1875345 bytes
ThroughPut:8.32712e-10 (GiB/sec)=8.52697e-07 MiB/sec

Error tolerance:0.001
compression ratio: 8.89416
8.38861e+06 bytes -> 943159 bytes
ThroughPut:8.34312e-10 (GiB/sec)=8.54336e-07 MiB/sec

Error tolerance:0.01
compression ratio: 36.0326
8.38861e+06 bytes -> 232806 bytes
ThroughPut:8.34936e-10 (GiB/sec)=8.54975e-07 MiB/sec

Error tolerance:0.1
compression ratio: 241.364
8.38861e+06 bytes -> 34755 bytes
ThroughPut:8.33867e-10 (GiB/sec)=8.5388e-07 MiB/sec

Error tolerance:1
compression ratio: 2009.73
8.38861e+06 bytes -> 4174 bytes
ThroughPut:8.34312e-10 (GiB/sec)=8.54336e-07 MiB/sec

### datasize = 0.0625GiB
Error tolerance:1e-13
compression ratio: 1.17306
6.71089e+07 bytes -> 57208171 bytes
ThroughPut:8.15927e-10 (GiB/sec)=8.35509e-07 MiB/sec

Error tolerance:1e-12
compression ratio: 1.08032
6.71089e+07 bytes -> 62119171 bytes
ThroughPut:8.18448e-10 (GiB/sec)=8.38091e-07 MiB/sec

Error tolerance:1e-11
compression ratio: 1.05168
6.71089e+07 bytes -> 63811364 bytes
ThroughPut:8.19296e-10 (GiB/sec)=8.38959e-07 MiB/sec

Error tolerance:1e-10
compression ratio: 1.09091
6.71089e+07 bytes -> 61516476 bytes
ThroughPut:8.18738e-10 (GiB/sec)=8.38388e-07 MiB/sec

Error tolerance:1e-09
compression ratio: 1.16108
6.71089e+07 bytes -> 57798758 bytes
ThroughPut:8.17442e-10 (GiB/sec)=8.37061e-07 MiB/sec

Error tolerance:1e-08
compression ratio: 1.39239
6.71089e+07 bytes -> 48196739 bytes
ThroughPut:8.16972e-10 (GiB/sec)=8.36579e-07 MiB/sec

Error tolerance:1e-07
compression ratio: 1.83035
6.71089e+07 bytes -> 36664558 bytes
ThroughPut:8.18288e-10 (GiB/sec)=8.37927e-07 MiB/sec

Error tolerance:1e-06
compression ratio: 2.33995
6.71089e+07 bytes -> 28679591 bytes
ThroughPut:8.19028e-10 (GiB/sec)=8.38684e-07 MiB/sec

Error tolerance:1e-05
compression ratio: 3.11805
6.71089e+07 bytes -> 21522713 bytes
ThroughPut:8.21061e-10 (GiB/sec)=8.40767e-07 MiB/sec

Error tolerance:0.0001
compression ratio: 4.63624
6.71089e+07 bytes -> 14474838 bytes
ThroughPut:8.21579e-10 (GiB/sec)=8.41297e-07 MiB/sec

Error tolerance:0.001
compression ratio: 9.31248
6.71089e+07 bytes -> 7206336 bytes
ThroughPut:8.22726e-10 (GiB/sec)=8.42471e-07 MiB/sec

Error tolerance:0.01
compression ratio: 39.686
6.71089e+07 bytes -> 1690994 bytes
ThroughPut:8.22552e-10 (GiB/sec)=8.42294e-07 MiB/sec
Error tolerance:0.1
compression ratio: 279.184
6.71089e+07 bytes -> 240375 bytes
ThroughPut:8.22801e-10 (GiB/sec)=8.42549e-07 MiB/sec

Error tolerance:1
compression ratio: 2478.72
6.71089e+07 bytes -> 27074 bytes
ThroughPut:8.22509e-10 (GiB/sec)=8.42249e-07 MiB/sec

## GPUs (Normal MGARD CUDA version)


## omp (MGARD-X) on monaka (16 cores)
### datasize: 0.0078125 GiB
tol=1e-12
exetime:0.584 sec
size: 0.0078125 GiB
comp ratio: 1.98051
Throughput: 0.0133776GiB/sec

tol=1e-11
exetime:0.594 sec
size: 0.0078125 GiB
comp ratio: 1.9805
Throughput: 0.0131524GiB/sec

tol=1e-10
exetime:0.621 sec
size: 0.0078125 GiB
comp ratio: 1.9805
Throughput: 0.0125805GiB/sec

tol=1e-09
exetime:0.579 sec
size: 0.0078125 GiB
comp ratio: 1.98054
Throughput: 0.0134931GiB/sec

tol=1e-08
exetime:0.679 sec
size: 0.0078125 GiB
comp ratio: 1.98088
Throughput: 0.0115059GiB/sec

tol=1e-07
exetime:0.677 sec
size: 0.0078125 GiB
comp ratio: 1.98333
Throughput: 0.0115399GiB/sec

tol=1e-06
exetime:0.917 sec
size: 0.0078125 GiB
comp ratio: 2.00958
Throughput: 0.00851963GiB/sec

tol=1e-05
exetime:0.876 sec
size: 0.0078125 GiB
comp ratio: 2.25195
Throughput: 0.00891838GiB/sec

tol=0.0001
exetime:0.855 sec
size: 0.0078125 GiB
comp ratio: 5.85699
Throughput: 0.00913743GiB/sec

tol=0.001
exetime:0.93 sec
size: 0.0078125 GiB
comp ratio: 21.3795
Throughput: 0.00840054GiB/sec

tol=0.01
exetime:0.591 sec
size: 0.0078125 GiB
comp ratio: 31.1666
Throughput: 0.0132191GiB/sec

tol=0.1
exetime:0.469 sec
size: 0.0078125 GiB
comp ratio: 50.6357
Throughput: 0.0166578GiB/sec

tol=1
exetime:0.485 sec
size: 0.0078125 GiB
comp ratio: 130.898
Throughput: 0.0161082GiB/sec

tol=10
exetime:0.44 sec
size: 0.0078125 GiB
comp ratio: 202.653
Throughput: 0.0177557GiB/sec

### datasize : 0.0625GiB
tol=1e-12
exetime:3.607 sec
size: 0.0625 GiB
comp ratio: 1.98391
Throughput: 0.0173274GiB/sec

tol=1e-11
exetime:2.945 sec
size: 0.0625 GiB
comp ratio: 1.98391
Throughput: 0.0212224GiB/sec

tol=1e-10
exetime:3.036 sec
size: 0.0625 GiB
comp ratio: 1.98392
Throughput: 0.0205863GiB/sec

tol=1e-09
exetime:2.821 sec
size: 0.0625 GiB
comp ratio: 1.98396
Throughput: 0.0221553GiB/sec

tol=1e-08
exetime:3.106 sec
size: 0.0625 GiB
comp ratio: 1.98432
Throughput: 0.0201223GiB/sec

tol=1e-07
exetime:3.945 sec
size: 0.0625 GiB
comp ratio: 1.98705
Throughput: 0.0158428GiB/sec

tol=1e-06
exetime:3.872 sec
size: 0.0625 GiB
comp ratio: 2.0114
Throughput: 0.0161415GiB/sec

tol=1e-05
exetime:3.49 sec
size: 0.0625 GiB
comp ratio: 2.28298
Throughput: 0.0179083GiB/sec

tol=0.0001
exetime:2.494 sec
size: 0.0625 GiB
comp ratio: 5.96788
Throughput: 0.0250601GiB/sec

tol=0.001
exetime:2.318 sec
size: 0.0625 GiB
comp ratio: 22.3697
Throughput: 0.0269629GiB/sec

tol=0.01
exetime:2.181 sec
size: 0.0625 GiB
comp ratio: 33.1622
Throughput: 0.0286566GiB/sec

tol=0.1
exetime:1.919 sec
size: 0.0625 GiB
comp ratio: 55.6069
Throughput: 0.032569GiB/sec

tol=1
exetime:1.813 sec
size: 0.0625 GiB
comp ratio: 156.324
Throughput: 0.0344732GiB/sec

tol=10
exetime:1.851 sec
size: 0.0625 GiB
comp ratio: 245.133
Throughput: 0.0337655GiB/sec


### datasize : 0.5 GiB
tol=1e-13
exetime:27.542 sec
size: 0.5 GiB
comp ratio: 1.98436
Throughput: 0.0181541GiB/sec

tol=1e-12
exetime:27.742 sec
size: 0.5 GiB
comp ratio: 1.98434
Throughput: 0.0180232GiB/sec

tol=1e-11
exetime:23.483 sec
size: 0.5 GiB
comp ratio: 1.98434
Throughput: 0.021292GiB/sec

tol=1e-10
exetime:27.298 sec
size: 0.5 GiB
comp ratio: 1.98435
Throughput: 0.0183164GiB/sec

tol=1e-09
exetime:25.545 sec
size: 0.5 GiB
comp ratio: 1.9844
Throughput: 0.0195733GiB/sec

tol=1e-08
exetime:28.365 sec
size: 0.5 GiB
comp ratio: 1.98487
Throughput: 0.0176274GiB/sec

tol=1e-07
exetime:26.079 sec
size: 0.5 GiB
comp ratio: 1.98821
Throughput: 0.0191725GiB/sec

tol=1e-06
exetime:25.15 sec
size: 0.5 GiB
comp ratio: 2.0139
Throughput: 0.0198807GiB/sec

tol=1e-05
exetime:23.318 sec
size: 0.5 GiB
comp ratio: 2.27177
Throughput: 0.0214427GiB/sec

tol=0.0001
exetime:16.048 sec
size: 0.5 GiB
comp ratio: 6.08189
Throughput: 0.0311565GiB/sec

tol=0.001
exetime:14.207 sec
size: 0.5 GiB
comp ratio: 22.2624
Throughput: 0.0351939GiB/sec

tol=0.01
exetime:12.9 sec
size: 0.5 GiB
comp ratio: 33.3198
Throughput: 0.0387597GiB/sec

tol=0.1
exetime:13.688 sec
size: 0.5 GiB
comp ratio: 57.5798
Throughput: 0.0365283GiB/sec

tol=1
exetime:12.14 sec
size: 0.5 GiB
comp ratio: 165.662
Throughput: 0.0411862GiB/sec

tol=10
exetime:13.219 sec
size: 0.5 GiB
comp ratio: 251.501
Throughput: 0.0378243GiB/sec

## single thread (MGARD-X)


## GPUs (MGARD-X)

# decompression
## single thread (Normal MGARD)

tol=1
tol=0.1
tol=0.01
tol=0.001
tol=0.0001

## GPUs (Normal MGARD CUDA version) datasize=2Gib a100 40GB
しゅばむが使っていますと。だから少し遅くはなっている。
### tol=1
1.12423GB/sec

### tol=0.5
1.08284GB/sec

### tol0.25
1.00251GB/sec

### tol=0.1
1.09111GB/sec

### tol=0.01
0.875657GB/sec

### tol=0.001
0.662032GB/sec

### tol=0.0001
0.630517GB/sec

### tol=0.00001
0.373692GB/sec

## omp (MGARD-X) datasize = 2GiB core = 16cores
### tol=1
0.0753352GB/sec

### tol=0.1
0.0689941GB/sec

### tol=0.01
0.0711642GB/sec

### tol=0.001
0.0656168GB/sec

### tol=0.0001
0.062081GB/sec

### tol=0.00001
0.0609347GB/sec

## single thread (MGARD-X) size = 2GiB
### tol=1
0.0126406GB/sec

### tol=0.1
0.0121111GB/sec

### tol=0.01
0.0124787GB/sec

### tol=0.001
0.0116484GB/sec

### tol=0.0001
0.0112705GB/sec

### tol=0.00001
0.0110972GB/sec


## GPUs (MGARD-X)

# refactoring

## MGARD-DR : Full-featured CPU serial implementaion of multi-precision data refactoring (2021のSCで紹介されていた論文の実装)

## MGARD-XDR (MDR-X): GPU acceleratoed portable implementation of MDR. Key features are implemented with other features under development. (これも2021のSCで紹介されていた論文の実装のGPU版)

# reconstruction

## MGARD-DR : Full-featured CPU serial implementaion of multi-precision data refactoring (2021のSCで紹介されていた論文の実装)

## MGARD-XDR (MDR-X): GPU acceleratoed portable implementation of MDR. Key features are implemented with other features under development. (これも2021のSCで紹介されていた論文の実装のGPU版)

# network_band
## iperfを使ってmonakaとclioneの間のバンド幅を測定した結果
934 MiBits/sec = 0.116375 GiB/sec、という感じですね。これだいぶ遅いですね。やはりネットワークボトルネックになりますよねー。
ちなみに、1Gbit =  0.1164 GiB.です。まあ、つまり、研究室のネットワークはほぼ1Gbit etherってことですね。
