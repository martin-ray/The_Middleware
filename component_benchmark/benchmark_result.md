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
Execution time: 9429 milliseconds
Error tolerance:1e-13
compression ratio: 1.17761
8.38861e+06 bytes -> 7123433 bytes
ThroughPut:8.28561e-10 (GiB/sec)=8.48446e-07 MiB/sec

Execution time: 9410 milliseconds
Error tolerance:1e-12
compression ratio: 1.08292
8.38861e+06 bytes -> 7746281 bytes
ThroughPut:8.30234e-10 (GiB/sec)=8.50159e-07 MiB/sec

Execution time: 9407 milliseconds
Error tolerance:1e-11
compression ratio: 1.05097
8.38861e+06 bytes -> 7981810 bytes
ThroughPut:8.30499e-10 (GiB/sec)=8.50431e-07 MiB/sec

Execution time: 9402 milliseconds
Error tolerance:1e-10
compression ratio: 1.08583
8.38861e+06 bytes -> 7725557 bytes
ThroughPut:8.3094e-10 (GiB/sec)=8.50883e-07 MiB/sec

Execution time: 9432 milliseconds
Error tolerance:1e-09
compression ratio: 1.14625
8.38861e+06 bytes -> 7318288 bytes
ThroughPut:8.28297e-10 (GiB/sec)=8.48176e-07 MiB/sec

Execution time: 9553 milliseconds
Error tolerance:1e-08
compression ratio: 1.33074
8.38861e+06 bytes -> 6303720 bytes
ThroughPut:8.17806e-10 (GiB/sec)=8.37433e-07 MiB/sec

Execution time: 9511 milliseconds
Error tolerance:1e-07
compression ratio: 1.74303
8.38861e+06 bytes -> 4812672 bytes
ThroughPut:8.21417e-10 (GiB/sec)=8.41131e-07 MiB/sec

Execution time: 9447 milliseconds
Error tolerance:1e-06
compression ratio: 2.24316
8.38861e+06 bytes -> 3739643 bytes
ThroughPut:8.26982e-10 (GiB/sec)=8.4683e-07 MiB/sec

Execution time: 9386 milliseconds
Error tolerance:1e-05
compression ratio: 2.99821
8.38861e+06 bytes -> 2797871 bytes
ThroughPut:8.32357e-10 (GiB/sec)=8.52333e-07 MiB/sec

Execution time: 9382 milliseconds
Error tolerance:0.0001
compression ratio: 4.4731
8.38861e+06 bytes -> 1875345 bytes
ThroughPut:8.32712e-10 (GiB/sec)=8.52697e-07 MiB/sec

Execution time: 9364 milliseconds
Error tolerance:0.001
compression ratio: 8.89416
8.38861e+06 bytes -> 943159 bytes
ThroughPut:8.34312e-10 (GiB/sec)=8.54336e-07 MiB/sec

Execution time: 9357 milliseconds
Error tolerance:0.01
compression ratio: 36.0326
8.38861e+06 bytes -> 232806 bytes
ThroughPut:8.34936e-10 (GiB/sec)=8.54975e-07 MiB/sec

Execution time: 9369 milliseconds
Error tolerance:0.1
compression ratio: 241.364
8.38861e+06 bytes -> 34755 bytes
ThroughPut:8.33867e-10 (GiB/sec)=8.5388e-07 MiB/sec

Execution time: 9364 milliseconds
Error tolerance:1
compression ratio: 2009.73
8.38861e+06 bytes -> 4174 bytes
ThroughPut:8.34312e-10 (GiB/sec)=8.54336e-07 MiB/sec

### datasize = 0.0625GiB
Execution time: 76600 milliseconds
Error tolerance:1e-13
compression ratio: 1.17306
6.71089e+07 bytes -> 57208171 bytes
ThroughPut:8.15927e-10 (GiB/sec)=8.35509e-07 MiB/sec

Execution time: 76364 milliseconds
Error tolerance:1e-12
compression ratio: 1.08032
6.71089e+07 bytes -> 62119171 bytes
ThroughPut:8.18448e-10 (GiB/sec)=8.38091e-07 MiB/sec

Execution time: 76285 milliseconds
Error tolerance:1e-11
compression ratio: 1.05168
6.71089e+07 bytes -> 63811364 bytes
ThroughPut:8.19296e-10 (GiB/sec)=8.38959e-07 MiB/sec

Execution time: 76337 milliseconds
Error tolerance:1e-10
compression ratio: 1.09091
6.71089e+07 bytes -> 61516476 bytes
ThroughPut:8.18738e-10 (GiB/sec)=8.38388e-07 MiB/sec

Execution time: 76458 milliseconds
Error tolerance:1e-09
compression ratio: 1.16108
6.71089e+07 bytes -> 57798758 bytes
ThroughPut:8.17442e-10 (GiB/sec)=8.37061e-07 MiB/sec

Execution time: 76502 milliseconds
Error tolerance:1e-08
compression ratio: 1.39239
6.71089e+07 bytes -> 48196739 bytes
ThroughPut:8.16972e-10 (GiB/sec)=8.36579e-07 MiB/sec

Execution time: 76379 milliseconds
Error tolerance:1e-07
compression ratio: 1.83035
6.71089e+07 bytes -> 36664558 bytes
ThroughPut:8.18288e-10 (GiB/sec)=8.37927e-07 MiB/sec

Execution time: 76310 milliseconds
Error tolerance:1e-06
compression ratio: 2.33995
6.71089e+07 bytes -> 28679591 bytes
ThroughPut:8.19028e-10 (GiB/sec)=8.38684e-07 MiB/sec

Execution time: 76121 milliseconds
Error tolerance:1e-05
compression ratio: 3.11805
6.71089e+07 bytes -> 21522713 bytes
ThroughPut:8.21061e-10 (GiB/sec)=8.40767e-07 MiB/sec

Execution time: 76073 milliseconds
Error tolerance:0.0001
compression ratio: 4.63624
6.71089e+07 bytes -> 14474838 bytes
ThroughPut:8.21579e-10 (GiB/sec)=8.41297e-07 MiB/sec

Execution time: 75967 milliseconds
Error tolerance:0.001
compression ratio: 9.31248
6.71089e+07 bytes -> 7206336 bytes
ThroughPut:8.22726e-10 (GiB/sec)=8.42471e-07 MiB/sec

Execution time: 75983 milliseconds
Error tolerance:0.01
compression ratio: 39.686
6.71089e+07 bytes -> 1690994 bytes
ThroughPut:8.22552e-10 (GiB/sec)=8.42294e-07 MiB/sec

Execution time: 75960 milliseconds
Error tolerance:0.1
compression ratio: 279.184
6.71089e+07 bytes -> 240375 bytes
ThroughPut:8.22801e-10 (GiB/sec)=8.42549e-07 MiB/sec

Execution time: 75987 milliseconds
Error tolerance:1
compression ratio: 2478.72
6.71089e+07 bytes -> 27074 bytes
ThroughPut:8.22509e-10 (GiB/sec)=8.42249e-07 MiB/sec

## GPUs (Normal MGARD CUDA version)
## omp (MGARD-X)
## single thread (MGARD-X)
## GPUs (MGARD-X)

# decompression
## single thread (Normal MGARD)
## GPUs (Normal MGARD CUDA version)
## omp (MGARD-X)
## single thread (MGARD-X)
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
