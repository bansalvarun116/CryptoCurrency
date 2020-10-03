import hashlib
from uuid import uuid4
import json
import datetime
from flask import Flask, request , jsonify
from urllib.parse import urlparse
import requests


class central_currency:
    
    # 1. constructor 
    def __init__(self):
        self.chain=[]
        self.transaction=[{'sender':'rupee_crypto_created',
                           'reciver':'rbi_crypto',
                           'amount':100000,
                           'utxo_block':0,
                           'utxo_tranaction_index':0}]
        self.mempol=set()
        self.mempol.add(('rupee_crypto_created','rbi_crypto',100000,0,0))
        self.nodes=set()
        self.utxo_set=set()
        
        """
        self.utxo.set.add({'block_index':0,
                           'tranaction_index': 0,
                           'amount':100000,
                           'owner':'rupee_crypto_created'})
        """
        ###self.utxo_set.add((0,0,100000,'rupee_crypto_created'))
        ## rupee crypto created does need a utxo
        #gensis block creation 
        
        self.creat_block(proof=1,previous_hash=0)
    
    
    
    #2. creating a block / adding a block to a blockchain
        
    def create_block(self,proof,previous_hash):
        
        self.create_transaction_set()
        
        
        block={'datetime':datetime.datetime.now(),
               'index':len(self.chain)+1,
               'proof':proof,
               'previous_hash':previous_hash,
               'transaction':self.transaction}
        
        for i in range(len(self.transaction)):
            if(self.transaction[i]['sender']!="rupee_crypto_created"):
                self.utxo_set.remove((self.transaction[i]['utxo_block'],
                self.transaction[i]['utxo_transaction_index'],
                self.transaction[i]['amount'],
                self.transaction[i]['sender']))
            self.mempol.remove((self.transaction[i]['sender'],
                                self.transaction[i]['reciver'],
                                self.transaction[i]['amount'],
                                self.transaction[i]['utxo_block'],
                                self.transaction[i]['utxo_transaction_index']))
        self.transaction=[]
        for i in range(len(block['transaction'])):
            self.utxo_set.add((block['index'],i,
                              block['transaction'][i]['amount'],
                              block['transaction'][i]['reciver']))
            
        self.chain.append(block)
        return block
    
    
    
    def get_previous_block(self):
        return self.chain[-1]
   
    def get_chain(self):
        return self.chain
    
    def get_mempol(self):
        return self.mempol
    
    def get_utxos(self):
        return self.utxo_set
    
    def get_nodes(self):
        return self.nodes
    
    
    
    
    def proof_of_work( self, previous_proof):
        new_proof=1
        proof_found=False
        while not proof_found:
            hash_=hashlib.sha256(str(new_proof**2-previous_proof**2).encode()).hexdigest()
            if(hash_[:4]=="0000"):
                proof_found=True
            else:
                new_proof+=1
        return new_proof
    
    
    
    def hash(self,block):
        
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
     
        
    def add_node(self,address):
        parsed_url=urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
        
        
    def add_transactions_to_mempol(self,sender, reciver, amount, utxo_block_index, utxo_transaction_index):
        if (utxo_block_index,utxo_transaction_index,amount,sender) in self.utxo_set or sender =='rupee_crypto_created':
            self.mempol.add((sender,reciver,amount,utxo_block_index, utxo_transaction_index))
            return 1
        return 0
    
    def create_transaction_set(self):
        counter=0
        max_limit=50
        for i in self.mempol:
            if counter==max_limit:
                break
            self.transaction.append({'sender':i[0],
                                    'reciver':i[1],
                                    'amount':i[2],
                                    'utxo_block':i[3],
                                    'utxo_transaction_index':i[4]})
            counter+=1
        
        return 1
    
    
    def update_nodes(self,x):
        status=False
        if x==0:
            network=self.get_nodes()
        else:
            network=self.get_nodes()[:x]
        
        for node in network:
            response=requests.get(f'http:/{node}/get_nodes')
            if response.status_code==200:
                other_nodes=response.json()['nodes']
                for temp_node in other_nodes:
                    self.nodes.add(temp_node)
                    status=True
                
        return status
                    
    def update_lite_nodes(self,x):
        return self.update_nodes(x)
    
    def update_full_node(self):
        return self.update_nodes(0)
    
    def update_mempol(self,x):
        if(x==0):
            
            network=self.get_nodes()
        else:
            network=self.get_nodes()[:x]
        update = False
        for node in network:
            response=requests.get(f'http://{node}/get_mempol')
            other_mempol=response.json()['mempol']
            for temp_transaction in other_mempol:
                if (temp_transaction[3],temp_transaction[4],temp_transaction[2],temp_transaction[0]) in self.utxo_set:
                    self.mempol.add(temp_transaction)
                    update=True
        return update
    
    def update_complete_mempol(self):
        return self.update_mempol(0)
    
    def update_member_mempol(self,x):
        return self.update_mempol(x)
    
    def is_chain_valid(self,chain):
        previous_block=chain[0]
        curent_block_index=1
        temp_utxo_set=set()
        len_chian=len(chain)
        while curent_block_index != len_chian:
            if chain[curent_block_index]['previous_hash']!=self.hash(previous_block):
                return None
            proof_diff=chain[curent_block_index]['proof']**2-previous_block['proof']**2
            if hashlib.sha256(str(proof_diff).encode()).hexdigest[:4]!='0000':
                return None
            transaction_list=previous_block['transaction']
            i=-1
            for temp_transctions in transaction_list:
                i+=1
                utxo_tupple=(temp_transctions['utxo_block'],temp_transctions['utxo_transaction_index'],temp_transctions['amount'], temp_transctions['sender'])
                if (not utxo_tupple in temp_utxo_set) or temp_transctions['sender']=='rupee_crypto_created':
                    return None
                else:
                    if utxo_tupple[3]!='rupee_crypto_created':                                        
                        temp_utxo_set.remove(utxo_tupple)
                    
                    new_utxo_tupple=(curent_block_index,i,temp_transctions['amount'],temp_transctions['reciver'])
                    temp_utxo_set.add(new_utxo_tupple)
            previous_block=chain[curent_block_index]
            curent_block_index+=1
        
        return temp_utxo_set
    
    def replace_chain(self):
        network=self.nodes
        longest_chain=None
        utxo_set_1=None
        max_len=len(self.chain)
        for node in network:
            response=requests.get(f'http://{node}/get_chain')
            if response.status_code==200:
                length=response.json()['length']
                chain=response.json()['chain']
                new_utxo_set=self.is_chain_valid(chain)
                if length>max_len and new_utxo_set:
                    max_len=length
                    longest_chain=chain
                    utxo_set_1=new_utxo_set
        if longest_chain:
            self.chain=longest_chain
            self.utxo_set=utxo_set_1
            return True
        return False
    
    def check(self,block):
        for transaction in block['transaction']:
            temp_tupple=(transaction['utxo_block'],transaction['utxo_transaction_index'],transaction['amount'],transaction['sender'])
            if temp_tupple in self.utxo_set:
                continue
            else:
                return False
        return True
    
    def del_from_mempol(self,transaction):
        for temp_transaction in transaction:
            temp_tupple=(transaction['sender'],transaction['reciver'],transaction['amount'],transaction['utxo_block'],transaction['utxo_tranaction_index'])
            self.mempol.remove(temp_tupple)
        return 1
    
    def del_from_utxo_set(self,transaction):
        for temp_transaction in transaction:
            temp_tupple=(transaction['utxo_block'],transaction['utxo_transaction_index'],transaction['amount'],transaction['sender'])
            self.utxo_set.remove(temp_tupple)
        return 1
        
    
    
    
    
    def update_chain(self):
        current_hash=self.hash(self.get_previous_block())    
        network=self.nodes
        for node in network:
            response=request.get(f'http://{node}/get_latest_block')
            if response.status_code ==200:
                current_proof=self.get_previous_block()['proof']
                new_proof=response.json()['block']['proof']
                proof_diff=new_proof**2-current_proof**2
                hash_proof=hashlib.sha256(str(proof_diff).encode()).hexdigest()
                if response.json()['block']['previous_hash']==current_hash and hash_proof[:4]=='0000':
                    if self.check(response.json()['block']):
                        
                        self.chain.append(response.json()['block'])
                        self.del_from_mempol(response.json()['block']['transaction'])
                        self.del_from_utxo_set(response.json()['block']['transaction'])
                        return response.json()['block']
                    
        return  None
    
                    
        
            
                    



#############################################
        
    
    
app=Flask(__name__)
node_address= str(uuid4()).replace('-', '')
blockchain=central_currency()   

@app.route('/get_chain',method=['GET'])
def get_chain():
    chain=blockchain.get_chain()
    response={'chain':chain,
              'length':len(chain)}
    return jsonify(response), 200

@app.route('/get_latest_block', method=['GET'])
def get_latest_block():
    response={'block':blockchain.get_chain()[-1]}
    return jsonify(response),200

@app.route('/get_nodes',method=['GET'])
def get_nodes():
    nodes=blockchain.get_nodes()
    response={'nodes':nodes}
    return jsonify(response), 200

@app.route('/get_utxos',method=['GET'])
def get_utxos():
    utxo_set=blockchain.get_utxos()
    response={'utxos':utxo_set}
    return jsonify(response), 200

@app.route('/get_mempol',method=['GET'])
def get_mempol():
    mempol=blockchain.get_mempol()
    response={'mempol':mempol}
    return jsonify(response), 200


@app.route('/mine_block',method=['GET'])
def mine_block():
    previous_block=blockchain.get_previous_block()
    previous_proof=previous_block['proof']
    proof=blockchain.proof_of_work(previous_proof)
    previous_hash=blockchain.hash(previous_block)
    block=blockchain.create_block(proof, previous_hash)
    response={'msg':"great job!!! you have successfully mined a block  $$$$$",
              'block_index':block['index'],
              'block_timestamp':block['datetime'],
              'transactions_added':block['transaction'],
              'proof':block['proof'],
              'previous_hash':block['previous_hash'],
              }
    return jsonify(response),200

@app.route('/add_nodes', methods=['POST'])
def add_nodes():
    json=request.getjson()
    nodes=json.get('nodes')
    if nodes== None:
        return "NO NODDDESSSS",400
    
    for node in nodes:
        
        blockchain.add_node(node)
    response={'msg':"all the nodes are added successfully",
              'nodes':list(blockchain.nodes)}
    return jsonify(response),201
    

@app.route('/send_transaction',method=['POST'])
def send_transaction():
    json=request.getjson()
    transaction_key=['sender','receiver','amount','utxo_block_index','utxo_transaction_index']
    if not all(key in json for key in transaction_key):
        return 'Some elements of the transaction are missing', 400
    blockchain.add_transactions_to_mempol(json['sender'], json['reciver'],json['amount'], json['utxo_block_index'], json['utxo_transaction_index'])
    response={'msg':"added"}
    return jsonify(response),200

@app.route('/is_valid', methods=['GET'])  
def is_vaild():
    if blockchain.is_chain_valid(blockchain.chain):
        response={'msg':"yeah! its valid"}      
    else:
        response={'msg':"oppssss!! its invalid"}
    return jsonify(response),200

@app.route('/update_complete_nodes', methods=['GET'])
def update_complete_node():
    status=blockchain.update_complete_mempol()
    response={}
    if status:
        response['msg']='all the nodes are added successfull'
    else:
        response['msg']="some error occurred"
    return jsonify(response),200


@app.route('/update_lite_nodes', methods=['GET','POST'])
def update_lite_nodes():
    json=request.get()
    status = blockchain.update_lite_nodes(json['x'])
    response={}
    if status:
        response['msg']='all the nodes are added successfull'
    else:
        response['msg']="some error occurred"
    return jsonify(response),200
    
@app.route('/update_complete_mempol', methods=['GET'])
def update_complete_mempol():
    status=blockchain.update_complete_mempol()
    response={}
    if status:
        response['msg']='all the nodes are added successfull'
    else:
        response['msg']="some error occurred"
    return jsonify(response),200 
    
@app.route('/update_member_mempol', methods=['GET','POST'])
def update_member_mempol():
    json=request.get()
    status = blockchain.update_member_mempol(json['x'])
    response={}
    if status:
        response['msg']='all the nodes are added successfull'
    else:
        response['msg']="some error occurred"
    return jsonify(response),200   


@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200 
   

@app.route('/update_chain',method=['GET'])
def update_chain():
    is_chain_updated=blockchain.update_chain()
    response={}
    if is_chain_updated:
        response['block']=is_chain_updated
    else:
        response['msg']="no block found"
    return jsonify(response)

        

app.run(host = '0.0.0.0', port = 5001)

    




              
    
    
    
    
    
    
                                
            
            
        
    
        
    
    
                
    
    
        
        
