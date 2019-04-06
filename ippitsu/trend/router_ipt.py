import random
from flask import Flask, render_template, request,jsonify
app = Flask(__name__)
from flask_sqlalchemy import SQLAlchemy
import datetime
from sqlalchemy import and_,or_
import datetime
import logging
import json
#import rq
#from rq import Queue
#import redis
#from redis import Redis
from time import sleep  
import os
#from omoi import omoifc
from bs4 import BeautifulSoup
import requests

logging.basicConfig(filename="debug.log",
                    format="%(levelname)s %(asctime)s %(message)s",
                    datefmt="%m/%d/%Y %I:%M:%S %p",
                    level = logging.DEBUG,
                    filemode = "w")
logging.warning("opening")
logging.info("infomation")
logging.debug("debug")


#接続情報
db_uri = 'mysql+pymysql://root:root@db/paiza?charset=utf8'  # プロトコル://ユーザー@アドレス,?文字コード   ←dockerのとき
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri  # 上で入れたものをここで使う
db = SQLAlchemy(app)  # db変数は後で使う

#-------------------------------------------
#ここからオブジェクトを生成
#ここからオブジェクトを生成

class Art(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text())
    naiyo = db.Column(db.Text())
    ctime = db.Column(db.DateTime, nullable=False,server_default=db.text('CURRENT_TIMESTAMP'), server_onupdate=db.text('CURRENT_TIMESTAMP'))
    paint = db.Column(db.Text())

#-------------------------------------------
#メイン
@app.route('/')
def select_sql():
    art = Art.query.order_by( Art.id.desc() ).all()  # id降順
    print("●メインのところ art=", art, flush=True)
    #art = Art.query.order_by( Art.ctime.desc() ).all()  # 時間降順
    #art = Art.query.order_by( Art.ctime.desc() ).limit(20).all()  #20　限定


    mes = "Art.query"
    return render_template('main.html', message = mes, articles = art)



#-------------------------------------------
#メインに信長を表示
@app.route('/wiki')
def wiki():

    url = "https://ja.wikipedia.org/wiki/織田信長"
    resp = requests.get(url)
    bs = BeautifulSoup(resp.text, 'html.parser')

    name="aa"
    paint="1"
    return_data=[]
    for i,t in enumerate(bs.select("p")):
        tx=t.getText()
        #print(tx)
        ret = {"id":i,"name":name,"naiyo":tx,"paint":paint}
        return_data.append(ret)

    mes = "wiki"
    return render_template('main.html', message = mes, articles = return_data)




#メインのレスポンス
#--------------
#そのまま　main　に戻るもの（別画面不要）

#削除(post経由）
@app.route('/delete', methods=["POST"])
def delete():
    id = request.form["del"]
    #print(f"id={id}")
    iid = Art.query.get(id)
    print ("#削除(post経由) iid=",iid,flush=True)
    db.session.delete(iid)
    db.session.commit()

    art = Art.query.order_by( Art.ctime.desc()).all()
    #art = Art.query.order_by( Art.ctime.desc() ).limit(10).all()
    mes = "削除(post経由）"
    return render_template('main.html', message = mes, articles = art)


#削除(get経由)
@app.route('/del/<int:id>')
def dele(id):
    iid = Art.query.get(id)  #ここは寸止め　iidにはクエリーだけで、実行されない
    print ("#削除(get経由) iid=",iid,flush=True)
    db.session.delete(iid)
    db.session.commit()

    art = Art.query.order_by( Art.ctime.desc() ).all()
    #art = Art.query.order_by( Art.ctime.desc() ).limit(10).all()
    mes = "削除(get経由)"
    return render_template('main.html', message = mes, articles = art)



#------------ 第1エリア リスト用----------------------------
#ajax通信
#　　idからnum個分のデータを返す、現状ほぼ全部
#　　データが増えてきたらid=100から300個分のデータみたいな感じになると思うが
#　　　とりあえずそんなにデータがないので現状idは適当、num=40とかで呼ばれてくる

@app.route('/ajax1', methods=['POST'])
def ajax1():
    contents = request.json
    id = contents['id']#ここはつかわなくなった
    num= contents['num']
    print("●akax1のところ　id=",id)
    art = Art.query.order_by( Art.ctime.desc() ).all()
    #art = Art.query.filter(Art.id<=id).order_by( Art.ctime.desc() ).limit(num).all()
    #art = Art.query.order_by( Art.ctime.desc() ).limit(num).all()

    #ここでオブジェクト化している
    return_data={}
    for i in range (num):
        id = art[i].id
        naiyo = art[i].naiyo 
        name = art[i].name
        paint = art[i].paint
        ret = {"id":id,"name":name,"naiyo":naiyo,"paint":paint}
        return_data[i]=ret

    aa= jsonify(aokiSet=json.dumps(return_data))
    #print("   ●ajax1のところ　return_data=",return_data,flush=True)
    #結果　return_data= {0: {'id': 258, 'name': 'name4', 'naiyo': 'ewewewew', 'paint': '527 374 368 ... 142 2 -1 '}, 1: {'id': 151, 'name': '絵描きさん', 'naiyo': 'qqqq151', 'paint': '211 121 121 120 119....

    return aa


#------------ 第1エリア編集　読み込み用 ---------

"""
#ajax通信 ここが重い処理をやっている感じにする
#　　idを１つうけとって、そのdbのデータを返す
@app.route('/ajax1e', methods=['POST'])
def ajax1e():
    contents = request.json
    id = contents['id']

    rqのテスト用
    #環境変数
    #rr0=os.environ.get('RQ_AOKI')
    #rr1=os.environ.get('MYSQL_PORT') #: 3306
    #rr2=os.environ.get('MYSQL_DB') #: trend
    #print("●ajax1eのところ　環境変数取得後",rr0,rr1,rr2,flush=True)

    #redisの確認
    #r = redis.StrictRedis(host='localhost', port=6379, db=0)
    #r.set("KEYa", "VALUEaaa")
    #print("●ajax1eのところ",r.get("KEYa"),flush=True) 
    
    #接続
    #redis_conn = Redis()
    #print("●　接続のところ redis_conn=",redis_conn,flush=True) 
    #q = Queue(connection=redis_conn) 
    #print("●　接続のところ vars(q)=",vars(q),flush=True) 

    #エンキュー
    #job = q.enqueue(omoifc, 100000000)
    #print("●　エンキューのところ vars(job)=",vars(job),flush=True) 


    #エンキューしない場合
    #omoifc(100000000)

    art = Art.query.filter(Art.id==id).all()

    id = art[0].id
    naiyo = art[0].naiyo 
    name = art[0].name
    paint = art[0].paint
    ret = {"id":id,"name":name,"naiyo":naiyo,"paint":paint}
    
    aa= jsonify(aokiSet=json.dumps(ret))

    return aa

#rq 重い処理


def omoi(num):
    for i in range (num):
        i+=1
        if (i%10000000==0):
            print(i)
    return 7777


"""
#ajax通信 org
#　　idを１つうけとって、そのdbのデータを返す
@app.route('/ajax1e', methods=['POST'])
def ajax1e():
    contents = request.json
    id = contents['id']

    art = Art.query.filter(Art.id==id).all()

    id = art[0].id
    naiyo = art[0].naiyo 
    name = art[0].name
    paint = art[0].paint
    ret = {"id":id,"name":name,"naiyo":naiyo,"paint":paint}
    
    aa= jsonify(aokiSet=json.dumps(ret))

    return aa

#---------第１エリア　編集書き込み用--------
# ajax通信　するもの 第1エリアから
# データの書き込み　idとname、naiyoの書き換え
@app.route('/ajax1e_wr', methods=['POST'])
def ajax1e_wr():
    # データを受け取る
    contents = request.json
    id = contents['id']
    name = contents["name"]
    naiyo = contents["naiyo"]

    # dbに書き込み
    # art = Art() #インスタンス作成　★これだけはだめだ
    art = Art.query.get(id)  # 一回取り込んでおく　変更しないpaintもあるので
    art.name = name  # 変数セット
    art.naiyo = naiyo  # 変数セット
    #art.paint = value_list　#これは不要、すでにセットされているので
    db.session.commit()    #ここでdbに書く　　これだけでいい
    
    #帰り　ほとんど使わないのだが、ちゃんとやらないとエラーになる
    ret = {"id":id,"name":name,"naiyo":naiyo}
    aa= jsonify(aokiSet=json.dumps(ret))
    #print("   aa=",aa,flush=True)
    return aa



#------------ 第2エリア ----------------------------
#新規       非ajax
@app.route('/shinki', methods=["POST"])
def shinki():
    name_res = request.form["name"]
    naiyo_res = request.form["naiyo"]
    art = Art() 
    art.name = name_res
    art.naiyo = naiyo_res
 
    db.session.add(art)
    db.session.commit()

    art = Art.query.order_by(Art.ctime.desc()).all()
    mes = "shinki"

    return render_template('main.html', message = mes, articles = art)

#------------ 第3エリア ----------------------------
#ajax通信　するもの  第3エリアから
#　　idを１つうけとって、そのdbのデータを返す
@app.route('/ajax', methods=['POST'])
def ajax3():
    contents = request.json
    print("@/ajax contents=",contents)
    id = contents['id']
    print("@/ajax id=",id)

    #id = request.form["chk"]
    art = Art.query.get(id)
    naiyo = art.naiyo
    name = art.name
    paint = art.paint
    print("@/ajax naiyo=",naiyo)

    return_data = {"name":name,"id":id,"naiyo":naiyo,"paint":paint}
    aa= jsonify(aokiSet=json.dumps(return_data))
    print("   aa=",aa,flush=True)
    return aa

#-------------第４エリア---------------------------
#ajax通信　するもの 第４エリアから
#データの追加　書き込み
@app.route('/ajax4', methods=['POST'])
def ajax4():
    #データを受け取る
    value_list = request.json
    name_res = "name4"#ダミー
    naiyo_res = "naiyo4"#ダミー
    #name_res = request.form["name"]
    #naiyo_res = request.form["naiyo"]
    
    #dbに書き込み
    art = Art() 
    art.name = name_res
    art.naiyo = naiyo_res
    art.paint = value_list
    #ここでdbに追加書き込み　　
    db.session.add(art)
    db.session.commit()

    obj={"aoki_status":"ok"}
    return jsonify(js_d=json.dumps(obj))

#-----------------
#いったんは別画面になるものの、基本はメインのresであるもの

#チェック（post経由）
@app.route('/check', methods=["POST"])
def check():
    id = request.form["chk"]
    art = Art.query.get(id)
    return render_template('check.html',  art = art)

#チェック(get経由)
@app.route('/chk/<int:id>')
def chk(id):
    art = Art.query.get(id)
    return render_template('check.html',  art = art)

#-----------第６エリア-----------------------------
#ゆっくりみようチェック(post経由)
@app.route('/check_slowly', methods=["POST"])
def check_slow():
    print("ゆっくりのところ request=", request, flush=True)
    print("ゆっくりのところ vars(request)=", vars(request), flush=True)
    explain(request)
    print()
    import inspect
    print( "inspect()=", inspect.getmembers(request), flush=True)


    id = request.form["chk"]
    art = Art.query.get(id)
    return render_template('check_slowly.html',  art = art)

#さくらを見ようチェック(post経由)
@app.route('/check_sakura', methods=["POST"])
def check_sakura():
    id = request.form["chk"]
    art = Art.query.get(id)
    return render_template('check_sakura.html',  art = art)

#虫の動きを見ようチェック(post経由)
@app.route('/check_mushi', methods=["POST"])
def check_mushi():
    id = request.form["chk"]
    art = Art.query.get(id)
    return render_template('check_mushi.html',  art = art)



import types


def explain(item, shows_private=False, shows_method=False):
    '''
    与えた python オブジェクトの詳細を表示します。
    '''
    print('EXPLAIN ------------------')
    print(item)
    print(type(item))
    print('ATTRIBUTES:')
    for d in dir(item):
        if d == 'type':
            continue
        if not shows_private and d.startswith('_'):
            continue
        attr = getattr(item, d)
        if not shows_method and (
                isinstance(attr, types.MethodType) or
                isinstance(attr, types.BuiltinMethodType) or
                isinstance(attr, types.CoroutineType) or
                isinstance(attr, types.FunctionType) or
                isinstance(attr, types.BuiltinFunctionType) or
                isinstance(attr, types.GeneratorType)
        ):
            continue
        print('{}:\t{}'.format(d, attr))





#-----------第７エリア-----------------------------
#普通の検索
@app.route('/search', methods=["POST"])
def search():
    kensaku_res = request.form["kensaku"]
    ken="%" + kensaku_res + "%"
    #print(f"検索文字列={ken}")

    #articles = Art.query.filter(Art.naiyo.like('%ken%')).all()  #ここ
    articles = Art.query.filter(Art.naiyo.like(ken)).all()  
    message = Art.query.filter(Art.naiyo.like(ken))
    return render_template('search.html', message = message, articles = articles)

#人名検索
@app.route('/search2', methods=["POST"])
def search2():
    kensaku_res = request.form["kensaku2"]
    ken="%" + kensaku_res + "%"
    #print(f"検索文字列={ken}")    

    #articles = Art.query.filter(Art.naiyo.like('%ken%')).all()  
    articles = Art.query.filter(Art.name.like(ken)).all()  
    message = Art.query.filter(Art.name.like(ken))
    return render_template('search.html', message = message, articles = articles)


#さかのぼり検索
@app.route('/sck2', methods=["POST"])
def sck2():
    dn = request.form["del2"]
    now = datetime.datetime.now() 
    stt= now-datetime.timedelta(days=int(dn))
    s=str(stt)
    s2=str(now)
    articles = Art.query.filter(and_(Art.ctime >= s,Art.ctime<=s2)).all()
    message = Art.query.filter(and_(Art.ctime >= s,Art.ctime<=s2))
    return render_template('search.html', message = message, articles = articles)

#----------------------------------------
#新たなやりとり画面を必要とするもの

#アナログな気持ちも書き込みたい
# PC用　一筆書きのメインである　analog.html　を呼び出す
@app.route('/analog')
def analog():
    return render_template('analog.html', message ="analog_msg")

#アナログな気持ちも書き込みたい
# PC用　一筆書きのメインである　analog.html　を呼び出す
@app.route('/analog2')
def analog2():
    return render_template('dot17.html', message ="analog_msg")

# スマホ一筆書き　toc xx.html　を呼び出す
@app.route('/toc')
def toc():
    return render_template('toc.html', message ="スマホ用")

#スマホ絵描きさん、一筆書き終了時、データベースに保存するところ
@app.route('/toc_res', methods=["POST"])
def toc_res():
    message = "スマホ_res"
    value_list = request.form["tx"]
    print("value_list=",value_list )

    name_res = "スマホさん"
    naiyo_res = "naiyoは無いよう"
    
    art = Art() 
    art.name = name_res
    art.naiyo = naiyo_res
    art.paint = value_list
    #ここでdbに書く　　
    db.session.add(art)
    db.session.commit()
    #その後10個くらい最近の絵を表示する
    articles = Art.query.order_by(Art.ctime.desc()).limit(10).all()
    print("articles")
    #return " message = message, articles = articles"
 
    return render_template('cvs_ato.html', message = message, articles = articles)


#絵描きさん、一筆書き終了時、データベースに保存するところ
@app.route('/analog_res', methods=["POST"])
def analog_res():
    message = "analog_res"
    value_list = request.form["xx"]
    name_res = request.form["name"]
    naiyo_res = request.form["naiyo"]
    print("●analog_resの中　")
    print("   name_res=",name_res)
    
    art = Art() 
    art.name = name_res
    art.naiyo = naiyo_res
    art.paint = value_list
    #ここでdbに書く　　
    db.session.add(art)
    db.session.commit()
    #その後10個くらい最近の絵を表示する
    articles = Art.query.order_by(Art.ctime.desc()).limit(10).all()
    print(articles)
    return render_template('cvs_ato.html', message = message, articles = articles)

#絵描きさん
# 一筆書きのメインである　cvs.html　を呼び出す
#canvas
@app.route('/cvs')
def cvs():
    message = "canvas"
    return render_template('cvs.html', message = message)

#絵描きさん、一筆書き終了時、データベースに保存するところ
@app.route('/cvs_ato', methods=["POST"])
def cvs_ato():
    message = "cvs_ato"
    value_list = request.form["xx"]
    print(value_list)
    art = Art() 
    art.name = "絵描きさん"
    art.paint = value_list
    #ここでdbに書く　　
    db.session.add(art)
    db.session.commit()
    #その後10個くらい最近の絵を表示する
    articles = Art.query.order_by(Art.ctime.desc()).limit(10).all()
    print(articles)
    return render_template('cvs_ato.html', message = message, articles = articles)

#--------------以下はテスト用　
# (ブラウザからuriを手打ち）
@app.route('/show/<int:id>')
def show(id):
    message = "SHOW SQLAlchemy"
    art = Art.query.get(id)
    return render_template('view_player.html', message = message, art = art)


#ロギング
@app.route('/log')                                                                 
def index():                                                                    
    app.logger.debug('debug')                                                   
    app.logger.info('info')                                                     
    app.logger.warn('warn')                                                     
    app.logger.error('error')                                                   
    app.logger.critical('critical')                                                                                                                         
    return "logging"                                                            
#実行しても何も起こらない                   
#　https://docs.python.jp/3/howto/logging.html#logging-basic-tutorial

#以外と忘れていた超シンプルなやつ
@app.route('/log2')                                                                 
def index2():                                                                    
    return "log2"  


#sudo python3 xxx.pyで動かすときは↓がないと起動しない
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)#ここは　gcp用だがcud37でもおなじでOK
