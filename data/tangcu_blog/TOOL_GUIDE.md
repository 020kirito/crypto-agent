# CTF Crypto 工具使用指南

> 从糖醋小鸡块博客提取的工具使用经验

## CRYPTO

### OpenSSL

**使用次数**: 1

**使用场景**:

1. CTF&#123;&#125;） 题目给了一个音频，Audacity打开： 经典的音频隐写摩斯电码，但是敲完摩斯密码，最后得到的uuid少了一位， 私聊出题人拿flag即可 。 Easy_Shark 题目描述： 1 鲨鱼！嗷呜！ 题目给了一个流量文件，追踪tcp流能发现一段php代码： 可以看出，在openssl扩展有效时，这段代码对数据的解密方式为AES_128后base64，并且给了key的值...

---

## FACTORING

### FactorDB

**使用次数**: 8

**使用场景**:

1. 814118128802834719820426253836317043818687888302054465994498115387703382090351794495827905499417861507007863378916334790750453883661675063377 第一部分可以直接factordb分解出小因子，然后多素数RSA求解。第二部分共模攻击。 exp： 1 2 3 4 5...

2. &quot; &#123;n = &#125; &quot; , file=f) print ( f&quot; &#123;e = &#125; &quot; , file=f) print ( f&quot; &#123;c = &#125; &quot; , file=f) 按题目提示把n放到factordb上看看，可以发现： n = p^5 然后e果然也是p-1的因子，所以这个题估计是想要...

3. n =&#x27; , n) print ( &#x27;c =&#x27; , c) # n = 201354090531918389422241515534761536573 # c = 20442989381348880630046435751193745753 首先观察到n较小，因此可以直接factordb分解出p、q。然后就是普通Rabin加密，原理不详述了。 exp： 1 2 3 4 ...

**代码示例**:

```python
from Crypto.Util.number import *from tqdm import *from factordb.factordb import FactorDBfrom gmpy2 import *PKEY = 55208723145458976481271800608918815438075571763947979755496510859604544396672ENC = 127194641882350916936065994389482700479720132804140137082316257506737630761eh = int(bin(PKEY)[2:][-8:],2)*2**8nh = int(bin(PKEY)[2:][:-8],2)*2**8ch = int(bin(ENC)[2:],2)*2**8#part1 bruteforce to factor nfor nl in trange(2**7):    n = nh + 2*nl + 1    f = FactorDB(n)    f.connect()    fs = f.get_factor_
```

---

### CADO-NFS

**使用次数**: 3

**使用场景**:

1. c = &#125; &quot; , file=f) 这个题目没有什么东西要说，赛中因为这句： 1 assert len (flag) &lt;= 45 就一直以为flag虽然短，但怎么说也应该有三四十个字符，所以完全没往mitm上想。并且赛中的前一段时间解出这题的队伍一度很少，所以也很自然地就往cado、论文这种错误的方向上靠了。 exp： 1 2 3 4 5 6 7 8 9 10 11 12...

2. 四元数的dlp问题变成了矩阵dlp问题。 由于本题选用的数据恰好没有一次域$GF(p),GF(q)$下的特征值，因此无法利用jordan化将问题转化为求解方程组，一个简单的思路是直接利用矩阵行列式将问题转化为$GF(p),GF(q)$下乘法群的dlp问题，由于$p,q$均为256bit，因此需要利用cado-nfs求解出$s\%(p-1), s\%(q-1)$并CRT起来，大约可以获得有500bi...

3. 四元数的dlp问题变成了矩阵dlp问题。 由于本题选用的数据恰好没有一次域$GF(p),GF(q)$下的特征值，因此无法利用jordan化将问题转化为求解方程组，一个简单的思路是直接利用矩阵行列式将问题转化为$GF(p),GF(q)$下乘法群的dlp问题，由于$p,q$均为256bit，因此需要利用cado-nfs求解出$s\%(p-1), s\%(q-1)$并CRT起来，大约可以获得有500bi...

---

### YAFU

**使用次数**: 2

**使用场景**:

1. ，然后多素数RSA求解。第二部分共模攻击。 exp： 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 from Crypto.Util.number import * from gmpy2 import * #yafu c = 28535916699190273475273097091422420145718...

2. 1878446471676122069724608083578102382181382107225473535696274374370868301830807644939881080301668756603163431000745972823980427048672732291 e = 65537 yafu分解一下就能得到n的分解，直接解密即可(主要注意phi的求法)。 exp： 1 2 3 4 ...

---

## LATTICE

### BKZ

**使用次数**: 9

**使用场景**:

1. 用的优化，这样的优化本质上是做了一个类似$01$到$\frac{1}{2}, -\frac{1}{2}$的balance，因此提高了Gap，降低了求解SVP的难度。 第二个优化可能小众一点： 由于最后的问题在于约化能力，因此自然要选能求解短向量能力更强的算法，朴素一点讲的话就比如LLL求不出来就换成BKZ，BKZ做不出来就继续抬高blocksize，大多数师傅应该都这样做过。 对于这道题目来说可以...

2. ，但是在符合要求的情况下可以很快地实现blocksize较大的BKZ算法，而本题最终可以用blaster求解，在个人电脑跑的话大概五六分钟左右。 exp 1 2 3 4 5 6 7 8 9 10 11 12 13 from subprocess import check_output from re import findall def blaster ( M, b...

3. er = Matrix(GF(p),A).left_kernel().basis() T = block_matrix( [ [Matrix(ZZ,ker)], [identity_matrix(m)*p] ] ) #print(T.dimensions()) res = Matrix(ZZ,T).BKZ()[m-n] u = vector(GF(p),res) ub = u*vector(GF(...

**代码示例**:

```python
from subprocess import check_outputfrom re import findalldef blaster(M, block_size=40, bkz_tour=5):    z = &quot;[[&quot; + &quot;]\n[&quot;.join(&quot; &quot;.join(map(str, row)) for row in M) + &quot;]]&quot;    open(&quot;Lattice_test&quot;, &#x27;w&#x27;).write(z+&#x27;\n&#x27;)    ######################################## if need verbose, add &quot;-v&quot;    ret = check_output([        &quot;python3&quot;, &quot;./src/app.py&quot;,        &quot;-i&quot;, &quot;Lattice_test&quot;, &quot;-b&
```

---

### FLATTER

**使用次数**: 2

**使用场景**:

1. er import * from Crypto.Cipher import AES from hashlib import md5 from random import * from re import findall from subprocess import check_output def flatter ( M ): # compile https://github.com/keegan...

2. r , row)) for row in M) + &quot;]]&quot; ret = check_output([ &quot;flatter&quot; ], input =z.encode()) return matrix(M.nrows(), M.ncols(), map ( int , findall( b&quot;-?\\d+&quot; , ret))) N, n, q = ...

---

### fplll

**使用次数**: 1

**使用场景**:

1. ime( int (e)): break else : e += 1 d = inverse(e,phi) c1 = pow (c,d,n) flag = (c1+v)*inverse(u,n) % n print (long_to_bytes( int (flag))) #ASIS&#123;__fpLLL__4pPL1cA7!0n5_iN_RSA!!!&#125; flag中提到fpLLL的话...

**代码示例**:

```python
import itertoolsfrom Crypto.Util.number import *from tqdm import *u = 1462429177173255359388007765931796537885368646963625242711326952977985471932962383861842635724040143033586225507124897993946275538644782337485276659791768803892242293535522679957964876776825548307042572518152706215000123872096447939862588392736653305289270336986724756913886373602016050815040147667630379593859685646307913471020561969933852495456652645591262189417744078633139731004839760821762709078987432999550663454348821414654
```

---

## MATH

### SageMath

**使用次数**: 41

**使用场景**:

1. 意义上的Hensel Lift，对于$f$的一个解$x$，有迭代公式 x_{k+1}=x_k-f(x_k)·(f'(x_1))^{-1} \mod q^{k+1} 而在重根的情况下，存在 f'(x_1)≡0 \mod q, 我们没法直接进行Hensel Lift来获得$q^k$上的解$x$（这也是在SageMath中使用.roots函数会卡住的原因）。要在这个条件下对方程进行求解，我们就要想办法把...

2. 4 25 26 27 28 29 30 31 32 33 34 35 36 37 from pwn import * from ast import literal_eval context.log_level = &quot;critical&quot; #sh = process([&quot;sage&quot;, &quot;chal.sage&quot;]) sh = remote( &...

3. 意义上的Hensel Lift，对于$f$的一个解$x$，有迭代公式 x_{k+1}=x_k-f(x_k)·(f'(x_1))^{-1} \mod q^{k+1} 而在重根的情况下，存在 f'(x_1)≡0 \mod q, 我们没法直接进行Hensel Lift来获得$q^k$上的解$x$（这也是在SageMath中使用.roots函数会卡住的原因）。要在这个条件下对方程进行求解，我们就要想办法把...

**代码示例**:

```python
from Crypto.Util.number import *from gmpy2 import *import randomfrom secret import flagclass Lock:    def __init__(self, p, q) -> None:        while True:            self.p = p            self.q = q            self.n = self.p * self.q            self.e = random.randint(10**14, 10**15)                        if gcd(self.e, (self.p-1)*(self.q-1)) == 1:                self.d = invert(self.e, (self.p-1)*(self.q-1))                break        def lock(self, message: int) -> int:        assert 1 < me
```

---

### PARI/GP

**使用次数**: 19

**使用场景**:

1. es 2n}$是随机置换矩阵，给出其中一个密文矩阵，我们需要判断他是$enc_0$还是$enc_1$，连续成功100轮就可以获得flag。 思路 这个题是第一天晚上上的，还没来得及看题@dbt和@rec他们就很快做掉了，所以就赛后来复现一下。 由于接触过一点点编码，所以看到这题很容易联想到编码里$SGP$的情况，其中$S$就是题目中的$A$，是随机矩阵，而$P$则是题目中的$C$也就是置换矩阵，而...

2. 在下午就初现端倪，注意到puzzle D的答案内容是： 别的我就忍了，两个字母还不好爆？于是我和@pursuing一合计决定手动开爆，我从后面他从前面，这时候和公众号的聊天内容变成了这样： 爆完w的时候觉得这样还是有点繁琐，于是干脆直接上号摇人： 热心观众@hashhash正好没事，于是直接加入，他gpt了一个模拟鼠标键盘输入的脚本，然后事情就变成了这样： 几分钟之后我们拿到了pzd的内容XD： ...

3. + 97 ),end= &quot;&quot; ) #uvgbdzbihyfxvqipvvwxqnpwybaomhnibglpncsdohyespkglzbbfpgwxjsludjcyesphzlcsznuflejzezmnqpktbjbbajocrqlfzogrpuzwesgqbvhvzpongpdbewtihwvuwrgrzbmudnuaxgzgcknydxhhlqguabnjhczkrfj...

**代码示例**:

```python
-----BEGIN OPENSSH PRIVATE KEY-----b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAaAAAABNlY2RzYS1zaGEyLW5pc3RwMjU2AAAACG5pc3RwMjU2AAAAQQSw+Fs***rO9Hbzkm****Mty8NFeb6YZloHs2KWjK****iQ78pJR+6T**SRi***BU7c0Oilk61i/***04RGPrMPAAAAqBAHrdwQB63cAAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBLD4WzJfys**dvOSZwUo4y3**0V5vp****ezYpaMrvZYmJD**klH7pOztJGJ7+oFTtz****TrWL/vcTThE**sw8AAAAgaJN/R323SVkRTqxz******8ClkzgxdWidxNTrTdwYIcAAAAOa*********B****y**IBAg==-----END OPENSSH PRIVATE KEY-----
```

---

## PYTHON

### gmpy2

**使用次数**: 31

**使用场景**:

1. 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 from Crypto.Util.number import * from gmpy2 import * import random from secret import fl...

2. 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 from Pwn4Sage.pwn import * from Crypto.Util.number import * from gmpy2 import * r = remote( &quot;node4.anna.nssctf....

3. 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 from Crypto.Util.number import * from gmpy2 import * import random, os from hashlib impor...

**代码示例**:

```python
from Crypto.Util.number import *from gmpy2 import *import randomfrom secret import flagclass Lock:    def __init__(self, p, q) -> None:        while True:            self.p = p            self.q = q            self.n = self.p * self.q            self.e = random.randint(10**14, 10**15)                        if gcd(self.e, (self.p-1)*(self.q-1)) == 1:                self.d = invert(self.e, (self.p-1)*(self.q-1))                break        def lock(self, message: int) -> int:        assert 1 < me
```

---

### SymPy

**使用次数**: 17

**使用场景**:

1. n后a、b恢复很容易，就不展开讲了。 exp： 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 from Crypto.Util.number import * from gmpy2 import gcd from sympy import isprime c1,c2,c3,c4,c5,c6,c7 = [ 2885...

2. 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 from sympy.ntheory.modular import crt from Crypto.Util....

3. e, d, p, q, dp, dq, u = sk p = getPrime( 1024 ) dp = d %(p- 1 ) sk = (n, e, d, p, q, dp, dq, u) m = 5 c = pow (m,e,n) print (rsa_decrypt(c, sk)) from sympy.ntheory.modular import crt nlist = [p,q] cli...

**代码示例**:

```python
from Crypto.Util.number import getPrime, getStrongPrime, bytes_to_longfrom sympy import factorialfrom random import randintfrom secret import flagp, q = getStrongPrime(1024), getStrongPrime(1024)def RSAgen(e = None):    d = 0    if not e:        while(d.bit_length() < 2047):            e = getPrime(2047)            d = pow(e, -1, (p-1)*(q-1))    else:        d = pow(e, -1, (p-1)*(q-1))    return (p*q, p, q, e, d)n = p*qprint(f&#x27;&#123;n = &#125;&#x27;)key = RSAgen()k = randint(600, 1200)f = f
```

---

### Z3

**使用次数**: 7

**使用场景**:

1. IdF4uMFd4 decode it 拿去试着解一下base64： 还是有乱码，不过大概已经能猜到是数字还需要移位了，手动调整一下数字，能发现第一个数字8改为3时，能解密出{，因此数字还需要前移5位，最终的base64如下： 1 :Q Look at you~ this is flag: ZmxhZ3tZMFVfTVU1N181dDRuZF91UF9yMWdIdF9uMFd9 decode it...

2. 40个值，但是却给出了包含了128个初始S、B经gen函数生成的值的数组z。而gen函数看着很麻烦，实际上就是一个复杂LFSR的更新过程，所以其实也可以看作是模2下的一些简单运算。 因此，我们把隐去的40个值视作40个变量，实际上就是40个变量、128个方程的解方程问题。 而这种位运算的多变量方程，z3往往是很有效的。我也直接丢给z3就得到了解，本地测试如下： 1 2 3 4 5 6 7 8 9 ...

3. 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 from random import randint from z3 import * def gen ( S, B ): L = S[ 0 ] ^ S[ 7 ] ^ S[ 38 ] ^ S[ 70 ] ^ S[ 81 ] ^ S[ 96 ] N = S[ 0 ] ^ B[ 0 ...

**代码示例**:

```python
:Q Look at you~  this is flag: ZmxhZ3tZMFVfTVU1N181dDRuZF91UF9yMWdIdF9uMFd9 decode it
```

---

### pwntools

**使用次数**: 3

**使用场景**:

1. ，平替为pycryptodome即可)： 2021年“绿城杯”网络安全大赛-Misc-流量分析_夜白君的博客-CSDN博客 得到flag： flag： SICTF{88a39373-e204-43b6-b321-33ac8972fde9} QR_QR_QR 题目描述： 1 我就扫码而已啦！为什么要用pwntools？ 题目给了一个端口，先用xshell手动交互一下： 可以依稀看出是二维码的定位符，...

2. 梦想 题目来源：2023-CNSS-Summer 题目描述： 1 刚刚接触网络安全不久的 Shino 有一个成为 Crypto 方向专家的梦想，所以他写了一个很安全的加密算法，你可以帮他看看吗？ 端口： 1 nc 47.108.140.140 11037 Hint： 1 2 3 4 1、你可能需要pwntools 2、cnss&#123;a-zA-Z0-9_&#125; 保证&#125;只在 fl...

3. nss{“串后，继续构造下面字符串： 1 2 for i in table: flag = &quot;cnss&#123;1&quot; + i + chr ( 0 )* 100 + &quot;a&quot; 如此反复发送直至flag串已知的部分长度为24即可。 构造字符串并发送给靶机端需要用到pwntools，同时还有一些小细节需要注意，比如需要发送的是字节流而非字符串流。但是这些慢慢调试程...

**代码示例**:

```python
我就扫码而已啦！为什么要用pwntools？
```

---

### OWI

**使用次数**: 2

**使用场景**:

1. ----+&quot; ); write_stdout( &quot;&quot; ); else state := STORE_FLAG_WAIT; end if ; when MENU =&gt; write_stdout( &quot;Please select one of the following options:&quot; ); write_stdout( &quot;1) Off...

2. compressed by an algorithm import hashlib &#x27;&#x27;&#x27; I have a quantum computer and I use it to solve some of the problems in my work. The following is part of my work. In order to protect the ...

**代码示例**:

```python
# The code is compressed by an algorithmimport hashlib&#x27;&#x27;&#x27;I have a quantum computer and I use it to solve some of the problems in my work. The following is part of my work.In order to protect the privacy of my work, all variable names have been replaced with simple letters. I believe you have also a quantum computer. Now please prove to me that you have a quantum computer.&#x27;&#x27;&#x27;n = lambda q, r: q % rx = lambda y, z: y**zi = lambda j, k: j if not k else i(k, n(j, k))l = 
```

---

### PyCryptodome

**使用次数**: 2

**使用场景**:

1. 都没找到这种key文件怎么使用，思路也就暂时停滞了。 直到hint出现，那就直接搜索CobaltStrike，发现一道类似流量分析题，照着一步步做就有了(其中CS_Decrypt中有一个脚本用到M2Crypto库，但是pip不下来，搜索资料发现这个库停止更新很久了，可能python版本对不上，平替为pycryptodome即可)： 2021年“绿城杯”网络安全大赛-Misc-流量分析_夜白君的博客...

2. password和token尝试登录，当且仅当满足下列条件时获得flag： username是admin password是123456 我们的任务是对token做篡改，使得其解密后是我们需要的内容，而这种篡改很类似于CBC的字节翻转，似乎并没有多大难度。 但实际尝试的时候，发现CFB和CBC模式在pycryptodome的实现有很大不同，CFB模式并没有完全按照分组来，而是有一个参数为segme...

---

## REVERSE

### IDA Pro

**使用次数**: 9

**使用场景**:

1. ( &quot;🌶️ Chaotic Spark Ignition!&quot; ) for i in range ( 3 ): print (lemonpepper.Pepper(). list ()) print ( &quot;SHOVE PLATES INTO PORTAL! 🛸🍽️ VALIDATE 🍋🌶️ COMBO OR KITCHEN MELTDOWN! 💣💥&quot; ) as...

2. ) print ( &quot;------&quot; ) parameters = valid.valid(trained_phi, trained_e, n) y_valid = parameters[ 0 ] print ( &quot;The encrypted output in validation set is %s&quot; % hex (y_valid)) print ( &...

3. f6b45a90dc69 After training, the two naughty parameters are more and more normal. It &#x27;s closer to your target! ------ The encrypted output in validation set is 0x775cbee546e7579f0a69645b59f72f5c8...

**代码示例**:

```python
c = &quot;&quot;&quot;✧✡✭✡✮ ✣✴✯ ✤✶✬✬✱ ✬✤ ✱✦✢✥✮✯✧✧, ✴✬✷✯ ✡✧ ✣✴✯ ✶✡✰✴✣. ✡✣ ❂✢✡✮✰✧ ✩✬✸✤✬✢✣, ✤✦✡✣✴, ✦✮✱ ✩✬✮✤✡✱✯✮✩✯. ✡✣ ✰✡✲✯✧ ✳✧ ✰✳✡✱✦✮✩✯ ★✴✯✮ ★✯ ✦✢✯ ✶✬✧✣, ✦✮✱ ✰✡✲✯✧ ✧✳✷✷✬✢✣ ★✴✯✮ ★✯ ✦✢✯ ✦✤✢✦✡✱. ✦✮✱ ✣✴✯ ✸✬✸✯✮✣ ★✯ ✰✡✲✯ ✳✷ ✴✬✷✯, ★✯ ✰✡✲✯ ✳✷ ✬✳✢ ✶✡✲✯✧. ✣✴✯ ★✬✢✶✱ ★✯ ✶✡✲✯ ✡✮ ✡✧ ✱✡✧✡✮✣✯✰✢✦✣✡✮✰ ✡✮✣✬ ✦ ✷✶✦✩✯ ✬✤ ✸✦✶✡✩✯ ✦✮✱ ✴✦✣✢✯✱, ★✴✯✢✯ ★✯ ✮✯✯✱ ✴✬✷✯ ✦✮✱ ✤✡✮✱ ✡✣ ✴✦✢✱✯✢. ✡✮ ✣✴✡✧ ★✬✢✶✱ ✬✤ ✤✯✦✢, ✴✬✷✯ ✣✬ ✤✡✮✱ ❂✯✣✣✯✢, ❂✳✣ ✯✦✧✡✯✢ ✧✦✡✱ ✣✴✦✮ ✱✬✮✯, ✣✴✯ ✸✬✢✯ ✸✯✦✮✡✮✰✤✳✶ ✶✡✤✯ ✬✤ ✤✦✡✣✴ ★✡✶✶ ✸✦✥✯ ✶✡✤✯ ✸✯✦✮✡✮✰✤✳✶.✧✬✸✯✣✡✸✯✧ ★✯ 
```

---

## RSA

### RSA相关工具

**使用次数**: 44

**使用场景**:

1. 这次出了两个MT和3rdRSA，不过这一篇wp也包含yolbby的LFSRs。 3rdRSA 题目描述： 1 3rd’s Crypto checkin 题目： 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 from Crypto.Util.number im...

2. unlocked lock&#x27; ) if __name__ == &#x27;__main__&#x27; : main() 题目比较长，但流程并不复杂。首先生成两个1024bit的素数p、q，然后以此为基础，生成两个Lock类AliceLock与BobLock，Lock类中的数据包含以下RSA密钥对，并提供加密和解密操作： AliceLock:(n,e_1),(p,q,d_1) BobL...

3. 77的LWE样本)： 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 from sage.stats.distributions.discrete_gaussian_integer import DiscreteGaussianDistributionIntegerSampler from sage.crypto.lwe import LWE, samples ...

**代码示例**:

```python
from sage.stats.distributions.discrete_gaussian_integer import DiscreteGaussianDistributionIntegerSamplerfrom sage.crypto.lwe import LWE, samplesp = 0xfffffffffffffffffffffffffffffffeffffffffffffffffm,n = 32*4,77esz = 2**64F = GF(p)V = VectorSpace(F,n)D = DiscreteGaussianDistributionIntegerSampler(esz)#gen private_key slwe = LWE(n=n, q=p, D=D)s = lwe._LWE__s#gen samplesample = list(zip(*samples(m=m, n=n, lwe=lwe)))A,b = sample
```

---

### Boneh-Durfee

**使用次数**: 8

**使用场景**:

1. t; %(h2,r2,s2)) 题目看上去不算短，但其实对DSA比较熟悉的话，马上就可以看出这道题目的主体其实是一个线性k的DSA攻击，只是两个k的线性关系中，a被隐去了，所以就需要通过cry()函数提供的信息来解出。 而关于a的信息就是一个RSA加密结果，而在这个RSA加密中由于d较小，所以可以用boneh and durfee攻击得到d，然后就可以解密出a了。题目名字的not wiener也就...

2. _2br_1 \quad(mod\;q) 得到k过后随便带入一个式子就能得到x也就是flag。 exp： 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 from Crypto.Util.number import * #part1 get a(boneh and durfee) a = bytes_to_long( b&quot;6d70e7...

3. tography Stack Exchange 以上是对一些背景知识的简单介绍，接下来进入到解题环节。我们的目标就是，根据如下式子： ed \equiv 1 \quad(mod\;(p^2-1)(q^2-1)) 以及p，q低100位相等、d比较小的特性来想办法解出d。 而d比较小这一点，很容易联想到Boneh&amp;Duree做低解密指数攻击所做的构造多项式来进行copper的方法。首先把式子展...

**代码示例**:

```python
from Crypto.Util.number import *#part1 get a(boneh and durfee)a = bytes_to_long(b&quot;6d70e71d06e29c742b86a6da0108238e&quot;)#part2 DSA&#x27;s linear k attackp= 161310487790785086482919800040790794252181955976860261806376528825054571226885460699399582301663712128659872558133023114896223014064381772944582265101778076462675402208451386747128794418362648706087358197370036248544508513485401475977401111270352593919906650855268709958151310928767086591887892397722958234379q= 11158611469026101607567777
```

---

### Wiener Attack

**使用次数**: 7

**使用场景**:

1. 简单写一写题目wp。 not_wiener 题目： 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 from Crypto.Util...

2. 可以看出这道题目的主体其实是一个线性k的DSA攻击，只是两个k的线性关系中，a被隐去了，所以就需要通过cry()函数提供的信息来解出。 而关于a的信息就是一个RSA加密结果，而在这个RSA加密中由于d较小，所以可以用boneh and durfee攻击得到d，然后就可以解密出a了。题目名字的not wiener也就用在这里，因为d的界大概是0.273，超过了wiener要求的$ \frac{1}{...

3. 95794349015838868221686216396597327273110165922789814315858462049706255254066724012925815100434953821856854529753 &quot;&quot;&quot; 三组低解密指数的情况，用的是扩展的wiener攻击，wiki上对于原理介绍的很清晰就不在这里展开了，可以参考： 扩展维纳攻击 - CT...

---

