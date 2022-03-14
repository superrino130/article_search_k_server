# article_search_k_server
`jPOST id` から `PubMed id` を探索するための `Ruby` 製のCGIツールです。
# gem
下記のgemが必要です。
```ruby
gem "bio"
gem "mechanize"
```
# shebang
開発環境に合わせて変更してください。
```ruby
#!C:/Ruby27-x64/bin/ruby
```
# jPOST
jPOSTから情報を取得します。
```ruby
----- jPOST info -----
JPST000855 PXD019396 createdDate: 2020-05-27
pi: Matthew D. Hirschey[AU] sm: Paul Grimsrud[AU]
[ Cyclin F (CCNF), Sirtuin 5 (SIRT5), cell cycle, ubiquitin, metabolism ]
```
# google scholar
```ruby
--- google scholar ---
https://scholar.google.com/scholar?hl=ja&q=JPST000855+OR+PXD019396

https://www.ncbi.nlm.nih.gov/pmc/articles/pmc8093487/
https://journals.asm.org/doi/abs/10.1128/MCB.00269-20
```
短時間で検索を行いますと、ロボットではないことの証明を要求されます
# pubmed
`PubMed`で`PI名` `SM名` `CreatedDate`の１か月前から１３か月後の`PubMed id`を取得します。
**注意　pi/sm ともそれぞれ1000件を上限として検索しています。**
**pi/sm の件数を合算し100件を超えた場合、番号の若い順に100件として検索しています。**
`PubMed id`から`Abstract`を取得し、`Keywords`の一致する点数を数えます。
`Keywords`が一致しない`PubMed id`は非表示となります。
`pi+sm`は双方の名前が論文に記載されていたケースになります。
```ruby
------- PubMed -------
from 2020/04/01 to 2021/06/01
10 papers hit
33168699
["pi+sm", "Sirtuin 5 (SIRT5)", "cell cycle", "ubiquitin", "metabolism"]
33243834
["pi", "metabolism"]
32691018
["pi", "metabolism"]
32660330
["sm", "metabolism"]
33466329
["pi", "metabolism"]
```
# 補足
