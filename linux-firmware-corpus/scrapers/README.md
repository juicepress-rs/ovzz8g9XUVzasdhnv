# scrapers

This subfolder archives all scrapers used to obtain the raw samples from all 17 vendors included in LFwC v2.0:

1.  [ASUS](https://www.asus.com)
3.  [D-Link](https://www.dlink.com/)
2.  [FRITZ!](https://fritz.com) (formerly [AVM](https://www.heise.de/en/news/AVM-gives-up-its-name-10509780.html))
4.  [EDIMAX](https://www.edimax.com/edimax/global/)
5.  [ENGENIUS](https://www.engeniustech.com)
6.  [Linksys](https://www.linksys.com/)
7.  [NETGEAR](https://netgear.com)
8.  [TP-Link](https://www.tp-link.com/)
9.  [TRENDnet](https://www.trendnet.com)
10. [Ubiquiti](https://www.ui.com)
11. [DrayTek](https://www.draytek.com/)
12. [Foscam](https://foscam.com/)
13. [MikroTik](https://mikrotik.com/)
14. [Moxa](https://www.moxa.com/)
15. [Netis](https://www.netis-systems.com/)
16. [TOTOLINK](https://www.totolink.net/)
17. [Zyxel](https://www.zyxel.com/)

## Note

The scrapers in this directory are for archival purposes and their use is discouraged.
They are no appropriate tool to replicate LFWC because website layouts change and sample availability fluctuates over time.
Thus, it is likely that various scrapers in this project do not work anymore.

To replicate the corpus, please refer to the autodownloader tools that work in conjunction with the `.csv` metadata we distribute.
They use the official direct download links and fall back to archive.org when the original source longer exists. Thanks!

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

For more information about scrapy, [see here.](https://docs.scrapy.org/en/latest/intro/install.html#intro-install)

## Use

```bash
scrapy crawl <scraper_name> -o <output.json>
```

## Available Scrapers

```plain
archive_avm
archive_draytek
archive_linksys
asus
avm
dlink
draytek
edimax
engenius
foscam
linksys
mikrotik
moxa
netgear
netis
totolink
tplink
trendnet
ubiquiti
zyxel
```
