# いろいろ説明
まず、tiledbはサーバではなく、ストレージエンジン、つまり、簡単に言うとライブラリです。ただ、s3にデータをためることができるようになっている。awsで契約するのはちょっと大変なので、minioっていう、s3互換のエンジンを使って、リモートからtiledbのデータを読み書きできるようにします。

# 環境の構築方法
## minio側
1. バイナリをインストールしてきてください。

2. オブジェクトストレージとして使うディレクトリを作ってください。普通にmkdirで。

3. ./minio server /path/to/the/backet/dir 
でサーバをスタートできます。コンソール画面とエンドポイントはスタート時にわかります。

4. ブラウザでminioのダッシュボードにアクセスしてbucketを作ってください。

5. キーを発行してください。

## tiledb側

1. 
```
pip install tiledb
```
で一発インストール可能。

2. 以下のpythonスクリプトで実行可能

```


import tiledb
import numpy as np

# Create a TileDB config
config = tiledb.Config()

# Set Minio-specific configuration options
 

config["vfs.s3.scheme"] = "http"
config["vfs.s3.region"] = ""
config["vfs.s3.endpoint_override"] = "172.20.2.253:9000"
config["vfs.s3.use_virtual_addressing"] = "false"
config["vfs.s3.aws_access_key_id"] = "16LhDAkDBaILJPXiqEJL"
config["vfs.s3.aws_secret_access_key"] = "mbOwcKU2foJMnwXEOs0yLYYKKKOCTMhN4pcwlu5p"

# Create contex
ctx = tiledb.Ctx(config)

array_name = "s3://tiledb/test2"
timestep=256
x=1024
y=1024
z=1024
tiles = timestep*x*y*z

dom = tiledb.Domain(tiledb.Dim(name="dim1", domain=(timestep,x,y,z), tile=tiles, dtype="int32"))
attr = tiledb.Attr(name="data", dtype="float32")
schema = tiledb.ArraySchema(domain=dom, attrs=(attr,))

# Create the TileDB array
tiledb.Array.create(array_name, schema,ctx=ctx)

# Write data to the array
with tiledb.open(array_name, "w",ctx=ctx) as array:
    data = {
        "dim1": [1, 2, 3],
        "data": [1.1, 2.2, 3.3],
    }
    array[1:4] = data

```
詳しいいじり方は今後勉強します。

# TODO
1. tiledbのインターフェースの使い方を勉強 半日
2. tiledbに圧縮した科学技術データを流しこむ
3. ベンチマークを取る

以上