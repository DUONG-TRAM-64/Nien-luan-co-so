# Databricks notebook source
# DBTITLE 1,Lưu vào cache
lineitem_df.cache()
customer_df.cache()
orders_df.cache()
supplier_df.cache()
region_df.cache()

# COMMAND ----------

# DBTITLE 1,Chạy 22 câu truy vấn
import time
from pyspark.sql import SparkSession

# Khởi động Spark
spark = SparkSession.builder \
    .appName("TPCH truy van 2GB") \
    .getOrCreate()

# Danh sách các câu truy vấn TPCH
queries = [
   """
    CREATE OR REPLACE TEMP VIEW revenue0 AS
    SELECT
        l_suppkey AS supplier_no,
        SUM(l_extendedprice * (1 - l_discount)) AS total_revenue
    FROM
        lineitem
    WHERE
        l_shipdate >= DATE('1994-03-01')
        AND l_shipdate < ADD_MONTHS(DATE('1994-03-01'), 3)
    GROUP BY
        l_suppkey
   """
   ,
    """
select
	l_returnflag,
	l_linestatus,
	sum(l_quantity) as sum_qty,
	sum(l_extendedprice) as sum_base_price,
	sum(l_extendedprice * (1 - l_discount)) as sum_disc_price,
	sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,
	avg(l_quantity) as avg_qty,
	avg(l_extendedprice) as avg_price,
	avg(l_discount) as avg_disc,
	count(*) as count_order
from
	lineitem
where
	l_shipdate <= date '1998-12-01' - interval '97' day 
group by
	l_returnflag,
	l_linestatus
order by
	l_returnflag,
	l_linestatus;
"""
,
"""

select
	s_acctbal,
	s_name,
	n_name,
	p_partkey,
	p_mfgr,
	s_address,
	s_phone,
	s_comment
from
	part,
	supplier,
	partsupp,
	nation,
	region
where
	p_partkey = ps_partkey
	and s_suppkey = ps_suppkey
	and p_size = 40
	and p_type like '%STEEL'
	and s_nationkey = n_nationkey
	and n_regionkey = r_regionkey
	and r_name = 'ASIA'
	and ps_supplycost = (
		select
			min(ps_supplycost)
		from
			partsupp,
			supplier,
			nation,
			region
		where
			p_partkey = ps_partkey
			and s_suppkey = ps_suppkey
			and s_nationkey = n_nationkey
			and n_regionkey = r_regionkey
			and r_name = 'ASIA'
	)
order by
	s_acctbal desc,
	n_name,
	s_name,
	p_partkey;
"""
,
"""

select
	l_orderkey,
	sum(l_extendedprice * (1 - l_discount)) as revenue,
	o_orderdate,
	o_shippriority
from
	customer,
	orders,
	lineitem
where
	c_mktsegment = 'MACHINERY'
	and c_custkey = o_custkey
	and l_orderkey = o_orderkey
	and o_orderdate < date '1995-03-15'
	and l_shipdate > date '1995-03-15'
group by
	l_orderkey,
	o_orderdate,
	o_shippriority
order by
	revenue desc,
	o_orderdate;
"""
,
"""

select
	o_orderpriority,
	count(*) as order_count
from
	orders
where
	o_orderdate >= date '1995-03-01'
	and o_orderdate < date '1995-03-01' + interval '3' month
	and exists (
		select
			*
		from
			lineitem
		where
			l_orderkey = o_orderkey
			and l_commitdate < l_receiptdate
	)
group by
	o_orderpriority
order by
	o_orderpriority;
"""
,
"""

select
	n_name,
	sum(l_extendedprice * (1 - l_discount)) as revenue
from
	customer,
	orders,
	lineitem,
	supplier,
	nation,
	region
where
	c_custkey = o_custkey
	and l_orderkey = o_orderkey
	and l_suppkey = s_suppkey
	and c_nationkey = s_nationkey
	and s_nationkey = n_nationkey
	and n_regionkey = r_regionkey
	and r_name = 'AFRICA'
	and o_orderdate >= date '1993-01-01'
	and o_orderdate < date '1993-01-01' + interval '1' year
group by
	n_name
order by
	revenue desc;
"""
,
"""

select
	sum(l_extendedprice * l_discount) as revenue
from
	lineitem
where
	l_shipdate >= date '1993-01-01'
	and l_shipdate < date '1993-01-01' + interval '1' year
	and l_discount between 0.08 - 0.01 and 0.08 + 0.01
	and l_quantity < 24;
"""
,
"""

select
	supp_nation,
	cust_nation,
	l_year,
	sum(volume) as revenue
from
	(
		select
			n1.n_name as supp_nation,
			n2.n_name as cust_nation,
			extract(year from l_shipdate) as l_year,
			l_extendedprice * (1 - l_discount) as volume
		from
			supplier,
			lineitem,
			orders,
			customer,
			nation n1,
			nation n2
		where
			s_suppkey = l_suppkey
			and o_orderkey = l_orderkey
			and c_custkey = o_custkey
			and s_nationkey = n1.n_nationkey
			and c_nationkey = n2.n_nationkey
			and (
				(n1.n_name = 'VIETNAM' and n2.n_name = 'IRAN')
				or (n1.n_name = 'IRAN' and n2.n_name = 'VIETNAM')
			)
			and l_shipdate between date '1995-01-01' and date '1996-12-31'
	) as shipping
group by
	supp_nation,
	cust_nation,
	l_year
order by
	supp_nation,
	cust_nation,
	l_year;
"""
,
"""

select
	o_year,
	sum(case
		when nation = 'IRAN' then volume
		else 0
	end) / sum(volume) as mkt_share
from
	(
		select
			extract(year from o_orderdate) as o_year,
			l_extendedprice * (1 - l_discount) as volume,
			n2.n_name as nation
		from
			part,
			supplier,
			lineitem,
			orders,
			customer,
			nation n1,
			nation n2,
			region
		where
			p_partkey = l_partkey
			and s_suppkey = l_suppkey
			and l_orderkey = o_orderkey
			and o_custkey = c_custkey
			and c_nationkey = n1.n_nationkey
			and n1.n_regionkey = r_regionkey
			and r_name = 'MIDDLE EAST'
			and s_nationkey = n2.n_nationkey
			and o_orderdate between date '1995-01-01' and date '1996-12-31'
			and p_type = 'LARGE BURNISHED TIN'
	) as all_nations
group by
	o_year
order by
	o_year;
"""
,
"""

select
	nation,
	o_year,
	sum(amount) as sum_profit
from
	(
		select
			n_name as nation,
			extract(year from o_orderdate) as o_year,
			l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity as amount
		from
			part,
			supplier,
			lineitem,
			partsupp,
			orders,
			nation
		where
			s_suppkey = l_suppkey
			and ps_suppkey = l_suppkey
			and ps_partkey = l_partkey
			and p_partkey = l_partkey
			and o_orderkey = l_orderkey
			and s_nationkey = n_nationkey
			and p_name like '%medium%'
	) as profit
group by
	nation,
	o_year
order by
	nation,
	o_year desc;
"""
,
"""

select
	c_custkey,
	c_name,
	sum(l_extendedprice * (1 - l_discount)) as revenue,
	c_acctbal,
	n_name,
	c_address,
	c_phone,
	c_comment
from
	customer,
	orders,
	lineitem,
	nation
where
	c_custkey = o_custkey
	and l_orderkey = o_orderkey
	and o_orderdate >= date '1994-06-01'
	and o_orderdate < date '1994-06-01' + interval '3' month
	and l_returnflag = 'R'
	and c_nationkey = n_nationkey
group by
	c_custkey,
	c_name,
	c_acctbal,
	c_phone,
	n_name,
	c_address,
	c_comment
order by
	revenue desc;
"""
,
"""

select
	ps_partkey,
	sum(ps_supplycost * ps_availqty) as value
from
	partsupp,
	supplier,
	nation
where
	ps_suppkey = s_suppkey
	and s_nationkey = n_nationkey
	and n_name = 'FRANCE'
group by
	ps_partkey having
		sum(ps_supplycost * ps_availqty) > (
			select
				sum(ps_supplycost * ps_availqty) * 0.0001000000
			from
				partsupp,
				supplier,
				nation
			where
				ps_suppkey = s_suppkey
				and s_nationkey = n_nationkey
				and n_name = 'FRANCE'
		)
order by
	value desc;
"""
,
"""

select
	l_shipmode,
	sum(case
		when o_orderpriority = '1-URGENT'
			or o_orderpriority = '2-HIGH'
			then 1
		else 0
	end) as high_line_count,
	sum(case
		when o_orderpriority <> '1-URGENT'
			and o_orderpriority <> '2-HIGH'
			then 1
		else 0
	end) as low_line_count
from
	orders,
	lineitem
where
	o_orderkey = l_orderkey
	and l_shipmode in ('FOB', 'REG AIR')
	and l_commitdate < l_receiptdate
	and l_shipdate < l_commitdate
	and l_receiptdate >= date '1997-01-01'
	and l_receiptdate < date '1997-01-01' + interval '1' year
group by
	l_shipmode
order by
	l_shipmode;
"""
,
"""

select
	c_count,
	count(*) as custdist
from
	(
		select
			c_custkey,
			count(o_orderkey)
		from
			customer left outer join orders on
				c_custkey = o_custkey
				and o_comment not like '%special%deposits%'
		group by
			c_custkey
	) as c_orders (c_custkey, c_count)
group by
	c_count
order by
	custdist desc,
	c_count desc;
"""
,
"""

select
	100.00 * sum(case
		when p_type like 'PROMO%'
			then l_extendedprice * (1 - l_discount)
		else 0
	end) / sum(l_extendedprice * (1 - l_discount)) as promo_revenue
from
	lineitem,
	part
where
	l_partkey = p_partkey
	and l_shipdate >= date '1997-01-01'
	and l_shipdate < date '1997-01-01' + interval '1' month;
"""
,
"""
select
	s_suppkey,
	s_name,
	s_address,
	s_phone,
	total_revenue
from
	supplier,
	revenue0
where
	s_suppkey = supplier_no
	and total_revenue = (
		select
			max(total_revenue)
		from
			revenue0
	)
order by
	s_suppkey;

"""
,
"""

select
	p_brand,
	p_type,
	p_size,
	count(distinct ps_suppkey) as supplier_cnt
from
	partsupp,
	part
where
	p_partkey = ps_partkey
	and p_brand <> 'Brand#13'
	and p_type not like 'ECONOMY PLATED%'
	and p_size in (12, 14, 44, 9, 23, 29, 26, 47)
	and ps_suppkey not in (
		select
			s_suppkey
		from
			supplier
		where
			s_comment like '%Customer%Complaints%'
	)
group by
	p_brand,
	p_type,
	p_size
order by
	supplier_cnt desc,
	p_brand,
	p_type,
	p_size;
"""
,
"""

select
	sum(l_extendedprice) / 7.0 as avg_yearly
from
	lineitem,
	part
where
	p_partkey = l_partkey
	and p_brand = 'Brand#34'
	and p_container = 'LG BOX'
	and l_quantity < (
		select
			0.2 * avg(l_quantity)
		from
			lineitem
		where
			l_partkey = p_partkey
	);
"""
,
"""

select
	c_name,
	c_custkey,
	o_orderkey,
	o_orderdate,
	o_totalprice,
	sum(l_quantity)
from
	customer,
	orders,
	lineitem
where
	o_orderkey in (
		select
			l_orderkey
		from
			lineitem
		group by
			l_orderkey having
				sum(l_quantity) > 314
	)
	and c_custkey = o_custkey
	and o_orderkey = l_orderkey
group by
	c_name,
	c_custkey,
	o_orderkey,
	o_orderdate,
	o_totalprice
order by
	o_totalprice desc,
	o_orderdate;
"""
,
"""

select
	sum(l_extendedprice* (1 - l_discount)) as revenue
from
	lineitem,
	part
where
	(
		p_partkey = l_partkey
		and p_brand = 'Brand#22'
		and p_container in ('SM CASE', 'SM BOX', 'SM PACK', 'SM PKG')
		and l_quantity >= 5 and l_quantity <= 5 + 10
		and p_size between 1 and 5
		and l_shipmode in ('AIR', 'AIR REG')
		and l_shipinstruct = 'DELIVER IN PERSON'
	)
	or
	(
		p_partkey = l_partkey
		and p_brand = 'Brand#51'
		and p_container in ('MED BAG', 'MED BOX', 'MED PKG', 'MED PACK')
		and l_quantity >= 20 and l_quantity <= 20 + 10
		and p_size between 1 and 10
		and l_shipmode in ('AIR', 'AIR REG')
		and l_shipinstruct = 'DELIVER IN PERSON'
	)
	or
	(
		p_partkey = l_partkey
		and p_brand = 'Brand#33'
		and p_container in ('LG CASE', 'LG BOX', 'LG PACK', 'LG PKG')
		and l_quantity >= 20 and l_quantity <= 20 + 10
		and p_size between 1 and 15
		and l_shipmode in ('AIR', 'AIR REG')
		and l_shipinstruct = 'DELIVER IN PERSON'
	);
"""
,
"""

select
	s_name,
	s_address
from
	supplier,
	nation
where
	s_suppkey in (
		select
			ps_suppkey
		from
			partsupp
		where
			ps_partkey in (
				select
					p_partkey
				from
					part
				where
					p_name like 'deep%'
			)
			and ps_availqty > (
				select
					0.5 * sum(l_quantity)
				from
					lineitem
				where
					l_partkey = ps_partkey
					and l_suppkey = ps_suppkey
					and l_shipdate >= date '1997-01-01'
					and l_shipdate < date '1997-01-01' + interval '1' year
			)
	)
	and s_nationkey = n_nationkey
	and n_name = 'BRAZIL'
order by
	s_name;
"""
,
"""

select
	s_name,
	count(*) as numwait
from
	supplier,
	lineitem l1,
	orders,
	nation
where
	s_suppkey = l1.l_suppkey
	and o_orderkey = l1.l_orderkey
	and o_orderstatus = 'F'
	and l1.l_receiptdate > l1.l_commitdate
	and exists (
		select
			*
		from
			lineitem l2
		where
			l2.l_orderkey = l1.l_orderkey
			and l2.l_suppkey <> l1.l_suppkey
	)
	and not exists (
		select
			*
		from
			lineitem l3
		where
			l3.l_orderkey = l1.l_orderkey
			and l3.l_suppkey <> l1.l_suppkey
			and l3.l_receiptdate > l3.l_commitdate
	)
	and s_nationkey = n_nationkey
	and n_name = 'VIETNAM'
group by
	s_name
order by
	numwait desc,
	s_name;
"""
,
"""

select
	cntrycode,
	count(*) as numcust,
	sum(c_acctbal) as totacctbal
from
	(
		select
			substring(c_phone from 1 for 2) as cntrycode,
			c_acctbal
		from
			customer
		where
			substring(c_phone from 1 for 2) in
				('12', '20', '24', '22', '33', '16', '18')
			and c_acctbal > (
				select
					avg(c_acctbal)
				from
					customer
				where
					c_acctbal > 0.00
					and substring(c_phone from 1 for 2) in
						('12', '20', '24', '22', '33', '16', '18')
			)
			and not exists (
				select
					*
				from
					orders
				where
					o_custkey = c_custkey
			)
	) as custsale
group by
	cntrycode
order by
	cntrycode;
"""
#ketthuc 22 cau
]

# Biến để lưu tổng thời gian thực hiện và lưu thời gian cho từng truy vấn
total_execution_time = 0.0
execution_times = []  # Danh sách để lưu thời gian thực hiện của từng truy vấn

# Vòng lặp thực hiện các truy vấn
for i, query in enumerate(queries):
    query_name = f"query{i}"  
    print(f"Executing {query_name}...")

    start_time = time.time()

    if query_name == "query0":
        spark.sql(query)
    else:
        result = spark.sql(query)
        result.show(truncate=False)  # Hiển thị kết quả

    end_time = time.time()
    execution_time = end_time - start_time  
    total_execution_time += execution_time  

    # Lưu thời gian thực hiện vào danh sách
    execution_times.append((query_name, execution_time))

    print(f"Execution time for {query_name}: {execution_time:.2f} seconds")
    print("-" * 40)

# Chuyển danh sách thời gian thực hiện thành DataFrame của pandas
execution_times_df = pd.DataFrame(execution_times, columns=['Query Name', 'Execution Time (seconds)'])

# In ra bảng dữ liệu
print(execution_times_df)

# In ra tổng thời gian chạy
print(f"Tổng thời gian chạy: {total_execution_time:.2f} seconds")

# COMMAND ----------

# DBTITLE 1,Tempview

import time
import pandas as pd
lineitem_df.createOrReplaceTempView("lineitem")
supplier_df.createOrReplaceTempView("supplier")
customer_df.createOrReplaceTempView("customer")
orders_df.createOrReplaceTempView("orders")
nation_df.createOrReplaceTempView("nation")
part_df.createOrReplaceTempView("part")
partsupp_df.createOrReplaceTempView("partsupp")
region_df.createOrReplaceTempView("region")

# COMMAND ----------

# DBTITLE 1,Name cho cột
# 8 bảng 
orders_df = orders_df.toDF("o_orderkey", "o_custkey", "o_orderstatus", "o_totalprice", "o_orderdate",
                            "o_orderpriority", "o_clerk", "o_shippriority", "o_comment" , "final")

lineitem_df = lineitem_df.toDF("l_orderkey", "l_partkey", "l_suppkey", "l_lineitemid", "l_quantity",
                                "l_extendedprice", "l_discount", "l_tax", "l_returnflag",
                                "l_linestatus", "l_shipdate", "l_commitdate", "l_receiptdate",
                                "l_shipinstruct", "l_shipmode", "l_comment" , "final")


part_df = part_df.toDF("p_partkey", "p_name", "p_mfgr", "p_brand", "p_type",
                        "p_size", "p_container", "p_retailprice", "p_comment" , "final")

supplier_df = supplier_df.toDF("s_suppkey", "s_name", "s_address", "s_nationkey",
                                "s_phone", "s_acctbal", "s_comment" , "final")

customer_df = customer_df.toDF("c_custkey", "c_name", "c_address", "c_nationkey",
                                "c_phone", "c_acctbal", "c_mktsegment", "c_comment" , "final")

nation_df = nation_df.toDF("n_nationkey", "n_name", "n_regionkey", "n_comment" , "final")

region_df = region_df.toDF("r_regionkey", "r_name", "r_comment" , "final")

partsupp_df = partsupp_df.toDF("ps_partkey", "ps_suppkey", "ps_availqty", "ps_supplycost", "ps_comment" , "final")

# COMMAND ----------

# DBTITLE 1,tao session 2 GB
from pyspark.sql import SparkSession

# Khởi tạo Spark session
spark = SparkSession.builder \
    .appName("TPC-H 2GB") \
    .getOrCreate()

# Đọc dữ liệu từ các file với inferSchema=True
orders_df = spark.read.csv('dbfs:/FileStore/2GB/orders.tbl', sep='|', header=False, inferSchema=True)
lineitem_df = spark.read.csv('dbfs:/FileStore/2GB/lineitem.tbl', sep='|', header=False, inferSchema=True)
part_df = spark.read.csv('dbfs:/FileStore/2GB/part.tbl', sep='|', header=False, inferSchema=True)
supplier_df = spark.read.csv('dbfs:/FileStore/2GB/supplier.tbl', sep='|', header=False, inferSchema=True)
customer_df = spark.read.csv('dbfs:/FileStore/2GB/customer.tbl', sep='|', header=False, inferSchema=True)
nation_df = spark.read.csv('dbfs:/FileStore/2GB/nation.tbl', sep='|', header=False, inferSchema=True)
region_df = spark.read.csv('dbfs:/FileStore/2GB/region.tbl', sep='|', header=False, inferSchema=True)
partsupp_df = spark.read.csv('dbfs:/FileStore/2GB/partsupp.tbl', sep='|', header=False, inferSchema=True)
