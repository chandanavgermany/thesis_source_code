# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 10:26:02 2021

@author: q514347
"""
import json
import psycopg2
from bottle import run, post, request, response, get

def enable_cors(fn):
  def _enable_cors(*args, **kwargs):
      response.headers['Access-Control-Allow-Origin'] = '*'
      response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
      response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
      if request.method != 'OPTIONS':
          return fn(*args, **kwargs)
  return _enable_cors

def execute_post_query(query):
    try:
        conn = psycopg2.connect("dbname='petri_net' user='postgres' host='localhost' password='popup123'")
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close() 
        return True
    except:
        return False   
    
def execute_select_query(query):
    try:
       conn = psycopg2.connect("dbname='petri_net' user='postgres' host='localhost' password='popup123'")
       cursor = conn.cursor()
       cursor.execute(query)
       data = cursor.fetchall() 
       cursor.close()
       conn.close()
       return data   
    except:
        return None

def update_result(data):
    query = "INSERT INTO result_log(makespan, stock_cost, tardiness_cost, stability, schedule_type)" +\
             "Values("+ data['makespan'] +", data["+ data['stock_cost'] +", "+ data['tardiness_cost'] +", "+ data['stability'] +", '"+ data['schedule_type'] +"')"
    return execute_post_query(query)

def delete_production_status_value():
    query = "DELETE FROM production_status_value"
    return execute_post_query(query)

def update_production_status_value(data):
    query = "INSERT INTO production_status_value(production_status) Values('" + data['production_status'] + "')"
    return execute_post_query(query)

def update_product_performance(data):
    query = "INSERT INTO product_performance_log(prod_name, operation_place, started_at, left_at, job, operation, place_type, machine) Values('"+ data['prod_name']+"','"+ data['operation_place']+"', '"+ data['started_at']+"', '"+ data['left_at'] +"', "+ data['job'] +", "+data['operation']+", '"+ data['place_type'] +"', "+ data['machine'] +")"
    return execute_post_query(query)

def update_job_operation_value(data):
    prod_name = data['prod_name']
    operation = data['operation']
    finished_pieces = data['finished_pieces']
    remaining_pieces = data['remaining_pieces']
    query = "Update temp_schedule_log  SET finished_pieces=" + str(finished_pieces) + " ,  remaining_pieces="+ str(remaining_pieces) + "  WHERE  prod_name='" + prod_name +"' and  operation=" + str(operation)
    return execute_post_query(query)

def set_running_operation_on_machine_value(data):
    machine = data['machine']
    log = data['log']
    query = "INSERT INTO temp_run_op_machine(machine, machine_log) VALUES (" + str(machine) +", '"+log+"' )"
    return execute_post_query(query)

def update_stock_level_value(data):
    stock_id = data['stock_id']
    level = data['level']
    query = "UPDATE stock_info SET current_level=" + level + " WHERE stock_id='" + str(stock_id) + "'"
    return execute_post_query(query)

def update_machine_status_value(data):
    machine = data['machine']
    status = data['status']
    query = "UPDATE machine_info SET machine_status='" + status + "'  WHERE machine_id='" + str(machine) + "'"
    return execute_post_query(query)

###############machine#################
@enable_cors
@post('/set_machine_status')
def update_machine_status():
    try:
        data = json.loads(request.body.read())
        print(data)
        
        if data is None:
            raise ValueError
        else:
            response.headers['Content-Type'] = 'application/json'
            if (update_machine_status_value(data)):
                return json.dumps({'result': 'Success'})
            else:
                return json.dumps({'result': 'failure'})
    except:
        raise ValueError
     
@enable_cors
@get('/machine/<machine_id>')
def get_machine_status(machine_id):
    query = "SELECT * from machine_info where machine_id='"+ str(machine_id) + "'"
    print(query)
    data = execute_select_query(query)
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-cache'
    return json.dumps({'result': data})

################STOCKS##################
@enable_cors
@post('/set_stock_level')
def update_stock_status():
    try:
        data = json.loads(request.body.read())        
        if data is None:
            raise ValueError
        else:
            response.headers['Content-Type'] = 'application/json'
            if (update_stock_level_value(data)):
                return json.dumps({'result': 'Success'})
            else:
                return json.dumps({'result': 'failure'})
    except:
        raise ValueError
        
@enable_cors
@get('/stock/<stock_id>')
def get_stock(stock_id):
    query = "SELECT * from stock_info where stock_id='"+ str(stock_id) + "'"
    print(query)
    data = execute_select_query(query)
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-cache'
    return json.dumps({'result': data})

############# miscellaneous ############
@enable_cors
@post('/clear_machine_data')    
def clear_machine_data():
    query_machine = ["Delete From machine_info"]
    print(query_machine)
    for query in query_machine:
        execute_post_query(query)
    return json.dumps({'result': 'done'})

@enable_cors
@post('/set_production_status')
def update_production_status():
    try:
        data = json.loads(request.body.read())
        print(data)
        if data is None:
            raise Exception('Improper data')
        else:
            response.headers['Content-Type'] = 'application/json'
            if update_production_status_value(data):
                return json.dumps({'result': 'successfull !'})
            else:
                return json.dumps({'result': 'Unsuccessfull !'})
    except Exception as e:
        print(str(e))    
        
        
@enable_cors
@post('/delete_production_status')
def delete_production_status():
    try:
        response.headers['Content-Type'] = 'application/json'
        if delete_production_status_value():
            return json.dumps({'result': 'successfull !'})
        else:
            return json.dumps({'result': 'Unsuccessfull !'})
    except Exception as e:
        print(str(e))  
        
        
@enable_cors
@post('/clear_machine_stock_data/')    
def clear_machine_stock_data():
    query_machine = ["Delete From machine_info", "Delete from stock_info", 
                     "Delete from temp_schedule_log", "Delete from product_performance_log"]
    for query in query_machine:
        execute_post_query(query)
    return json.dumps({'result': 'done'})

@enable_cors
@post('/operation_status/')    
def update_operation_status():
    try: 
        data = json.loads(request.body.read())
        print(data)
        if data is None:
            raise Exception('Improper data')
        else:
            response.headers['Content-Type'] = 'application/json'
            if update_job_operation_value(data):
                return json.dumps({'result': 'successfull !'})
            else:
                return json.dumps({'result': 'Unsuccessfull !'})
    except Exception as e:
        print(str(e))
        
@enable_cors
@post('/product_performance_status/')    
def update_product_performance_status():
    try: 
        data = json.loads(request.body.read())
        print(data)
        if data is None:
            raise Exception('Improper data')
        else:
            response.headers['Content-Type'] = 'application/json'
            if update_product_performance(data):
                return json.dumps({'result': 'successfull !'})
            else:
                return json.dumps({'result': 'Unsuccessfull !'})
    except Exception as e:
        print(str(e))

@enable_cors
@post('/result_stats/')    
def update_result_stats():
    try: 
        data = json.loads(request.body.read())
        print(data)
        if data is None:
            raise Exception('Improper data')
        else:
            response.headers['Content-Type'] = 'application/json'
            if update_result(data):
                return json.dumps({'result': 'successfull !'})
            else:
                return json.dumps({'result': 'Unsuccessfull !'})
    except Exception as e:
        print(str(e))              
        
@enable_cors
@get('/production_status/')
def get_production_status(test):
    query = "Select * from temp_schedule_log where remaining_pieces != 0"
    data = execute_select_query(query)
    if len(data) == 0:
        data = "done"
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-cache'
    return json.dumps({'result': data})
        
##############################################
if __name__ == "__main__":
    run(host='localhost', port=8080, debug=True)