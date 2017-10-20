

import jieba
from jieba import 

class JiebaTokenizer(Tokenizer):
  def __init__(self):
    if ARGS.user_dict:
      print("Begin loading userdict from %s" % ARGS.user_dict)
      beg = time.time()
      jieba.load_userdict(ARGS.user_dict)
      end = time.time()
      print("Loading userdict completely. Total time cost: %.4f seconds." % (end-beg))

  def tokenize_file(self, f):
    frn = path.join(ARGS.input_dir, f)
    fwn = path.join(ARGS.output_dir, f)
    with open(fwn, 'w') as fw: 
      with open(frn) as fr: 
        for line in fr: 
          tokens = jieba.cut(line.rstrip('\r\n'))
          fw.write(' '.join(tokens)+'\n')
  
  def tokenize_list(self, input_files):
    cpu_count = multiprocessing.cpu_count()
    pool = ProcessingPool(min(cpu_count, len(input_files)))
    pool.map(self.tokenize_file, input_files)
    #pool.map(self.tokenize_file, zip([self]*len(input_files),input_files))
    pool.close()
    pool.join()

  def tokenize_date_range(self, beg_date_str, end_date_str):
    bvec = re.split('[\-_]+', beg_date_str)
    evec = re.split('[\-_]+', end_date_str)
    if len(bvec)!=3 or len(evec)!=3:
      print beg_date_str, bvec,"\n", end_date_str, evec
      print("usage:")
      print("  python jieba_tokenize.py [begin-date] [end-date]")
      print("  date format [YYYY-MM-DD]/[YYYY_MM_DD]\n")
      sys.exit()
    beg_date = datetime(int(bvec[0]), int(bvec[1]), int(bvec[2]))
    end_date = datetime(int(evec[0]), int(evec[1]), int(evec[2]))
    
    file_list = []
    delta = timedelta(days=1)
    cur_date = beg_date
    while cur_date <= end_date:
      tmp_date_str = ''.join(str(cur_date).split()[0].split('-'))
      cur_date += delta
      file_list.append(tmp_date_str)
    self.tokenize_list(file_list)






