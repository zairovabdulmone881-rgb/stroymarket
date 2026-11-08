import sys, os
sys.path.insert(0, os.getcwd())
import styles, badr3d as B
name=sys.argv[1]; styles.setup(name); B.PREFIX=name+"_"; B.main(sys.argv[2:])
