# 説明
## benchmarks dir
MGARDを使い、tolとSize, deviceTypeをパラメータにしたときの
各コンポーネントのバンド幅などを計測
これをもとにLatencyモデル

```
L (tol,OriSize) = OriSize/nvmeBw +  OriSize/CompBw + CompressedSize(tol,OriginalSize)/NetBw + CompressedSize(tol,OriginalSize)/DecompBw
```
を構築
また、zlibを使った時の圧縮と解凍のスループットも計測

さらに、psnrも計測した。

## images_by_tol
tolごとのimageを格納。

## Latency_model dir
上記のlatencyモデルを使いシミュレーションをした結果を格納

### latency_0921_reduced
tolの刻み幅が
[0.00001, 0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.5, 1]
と大きい感じ。GPUで計測

### Latency_0921
tolの刻み幅がめちゃめちゃ大きい

### Latency_single_reduced
single threadでの性能。


### 
